"""Safe Report Generator Service producing immutable JSON and safe styled HTML reports."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.errors import LuxException, NotFoundError
from app.models.investigation import Investigation, ReportArtifact
from app.models.pipeline import PipelineRun
from app.models.scenario import Scenario
from app.models.validation import ValidationFinding, ValidationRun
from app.schemas.investigation import _safe_parse_str_list
from app.schemas.report import (
    IncidentReportData,
    ReportFindingDetail,
    ReportFormat,
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportImpactedAsset,
    ReportPipelineSummary,
    ReportValidationSummary,
)
from app.schemas.validation import RuleStatus
from app.services.impact.analyzer import ImpactAnalysisService
from app.services.reports.investigation import InvestigationService

logger = logging.getLogger("lux.services.reports.generator")

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _safe_json_loads(val: Any, default: Any = None) -> Any:
    """Safely parse a JSON string, or return the default if parsing fails."""
    if val is None:
        return default
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        cleaned = val.strip()
        if not cleaned:
            return default
        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            return default
    return default


def _extract_evidence_samples(
    evidence_dict: dict[str, Any],
) -> tuple[list[str], list[int], list[dict[str, Any]]]:
    """Extract sample keys, line numbers, and sample records from structured evidence."""
    sample_keys: list[str] = []
    sample_lines: list[int] = []
    sample_records: list[dict[str, Any]] = []

    # 1. Extract sample keys
    for key in (
        "sample_orphaned_keys",
        "sample_keys",
        "duplicate_sample_keys",
        "sample_values",
        "violating_keys",
    ):
        val = evidence_dict.get(key)
        if isinstance(val, list):
            sample_keys.extend([str(k) for k in val if k is not None])

    # 2. Extract from sample_duplicates
    sample_dups = evidence_dict.get("sample_duplicates")
    if isinstance(sample_dups, list):
        for item in sample_dups:
            if isinstance(item, dict):
                for k, v in item.items():
                    if k.endswith("_id") or k in ("id", "key"):
                        sample_keys.append(str(v))
                row_indices = item.get("row_indices")
                if isinstance(row_indices, list):
                    sample_lines.extend([int(idx) for idx in row_indices if str(idx).isdigit()])
                sample_records.append(item)

    # 3. Extract sample violations or sample records
    for key in ("sample_violations", "sample_records", "violating_records", "negative_records"):
        val = evidence_dict.get(key)
        if isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    sample_records.append(item)

    # 4. Extract line numbers
    for key in ("sample_line_numbers", "line_numbers", "row_indices"):
        val = evidence_dict.get(key)
        if isinstance(val, list):
            sample_lines.extend([int(x) for x in val if str(x).isdigit()])

    # Deduplicate preserving order
    seen_keys: set[str] = set()
    deduped_keys: list[str] = []
    for k in sample_keys:
        if k not in seen_keys:
            seen_keys.add(k)
            deduped_keys.append(k)

    seen_lines: set[int] = set()
    deduped_lines: list[int] = []
    for line in sample_lines:
        if line not in seen_lines:
            seen_lines.add(line)
            deduped_lines.append(line)

    return deduped_keys, deduped_lines, sample_records


class ReportGeneratorService:
    """Domain service for generating immutable, reproducible, safe incident reports."""

    _jinja_env: Environment | None = None

    @classmethod
    def get_jinja_env(cls) -> Environment:
        """Get or initialize the secure Jinja2 environment with auto-escaping enabled."""
        if cls._jinja_env is None:
            cls._jinja_env = Environment(
                loader=FileSystemLoader(str(TEMPLATES_DIR)),
                autoescape=select_autoescape(
                    enabled_extensions=("html", "xml", "jinja2"),
                    default_for_string=True,
                    default=True,
                ),
            )
        return cls._jinja_env

    @classmethod
    def generate_report(
        cls,
        db: Session,
        request: ReportGenerateRequest,
    ) -> ReportGenerateResponse:
        """Generate and persist an immutable JSON and safe HTML incident report.

        Args:
            db: Active SQLAlchemy database session.
            request: Report generation request payload.

        Returns:
            ReportGenerateResponse with report identifier and download URLs.

        Raises:
            NotFoundError: If scenario, investigation, or validation run is not found.
        """
        # 1. Verify scenario exists
        scenario = db.scalar(select(Scenario).where(Scenario.id == request.scenario_id))
        if not scenario:
            raise NotFoundError(
                code="SCENARIO_NOT_FOUND",
                message=f"Scenario '{request.scenario_id}' was not found.",
                details={"scenario_id": request.scenario_id},
            )

        # 2. Resolve or create Investigation workspace
        investigation: Investigation
        if request.investigation_id:
            investigation = InvestigationService.get_investigation(
                db=db, investigation_id=request.investigation_id
            )
        else:
            # Auto-synthesize or create investigation workspace
            if request.verified_facts or request.hypotheses or request.action_items:
                from app.schemas.investigation import (
                    InvestigationCreateRequest,
                    InvestigationStatus,
                )

                create_req = InvestigationCreateRequest(
                    scenario_id=request.scenario_id,
                    title=request.title or f"Investigation: {scenario.name} Incident Analysis",
                    status=InvestigationStatus.OPEN,
                    verified_facts=request.verified_facts,
                    hypotheses=request.hypotheses,
                    action_items=request.action_items,
                )
                investigation = InvestigationService.create_investigation(db=db, request=create_req)
            else:
                investigation = InvestigationService.synthesize_investigation(
                    db=db, scenario_id=request.scenario_id, title=request.title
                )

        # 3. Resolve ValidationRun
        val_run: ValidationRun | None
        if request.validation_run_id:
            val_run = db.scalar(
                select(ValidationRun).where(ValidationRun.id == request.validation_run_id)
            )
            if not val_run:
                raise NotFoundError(
                    code="VALIDATION_RUN_NOT_FOUND",
                    message=f"Validation run '{request.validation_run_id}' was not found.",
                    details={"validation_run_id": request.validation_run_id},
                )
        else:
            # Fetch latest validation run for this scenario
            val_run = db.scalar(
                select(ValidationRun)
                .where(ValidationRun.scenario_id == request.scenario_id)
                .order_by(ValidationRun.executed_at.desc())
            )
            if not val_run:
                raise NotFoundError(
                    code="NO_VALIDATION_RUN_FOUND",
                    message=(
                        f"No validation runs found for scenario '{request.scenario_id}'. "
                        "Execute validations before generating a report."
                    ),
                    details={"scenario_id": request.scenario_id},
                )

        # 4. Fetch granular validation findings with eager-loaded rule relationship
        findings_query = (
            select(ValidationFinding)
            .options(joinedload(ValidationFinding.rule))
            .where(ValidationFinding.run_id == val_run.id)
            .order_by(ValidationFinding.created_at.asc())
        )
        findings_models = list(db.scalars(findings_query).unique().all())

        finding_details: list[ReportFindingDetail] = []
        first_failed_finding: ValidationFinding | None = None
        for f in findings_models:
            if f.status == RuleStatus.FAILED and first_failed_finding is None:
                first_failed_finding = f

            evidence_dict = _safe_json_loads(f.evidence, {})
            if not isinstance(evidence_dict, dict):
                evidence_dict = {}

            sample_keys, sample_lines, sample_records = _extract_evidence_samples(evidence_dict)

            rule_name = f.rule.name if f.rule else f.rule_id

            finding_details.append(
                ReportFindingDetail(
                    id=f.id,
                    rule_id=f.rule_id,
                    rule_name=rule_name,
                    category=f.rule_category,
                    severity=f.severity,
                    status=f.status,
                    dataset_id=f.dataset_id,
                    message=f.message,
                    affected_record_count=f.affected_record_count,
                    total_record_count=f.total_record_count,
                    sample_keys=sample_keys,
                    sample_line_numbers=sample_lines,
                    sample_records=sample_records,
                    created_at=f.created_at.isoformat() if f.created_at else "",
                )
            )

        # 5. Fetch latest pipeline run summary if available
        pipeline_run = db.scalar(
            select(PipelineRun)
            .where(PipelineRun.scenario_id == request.scenario_id)
            .order_by(PipelineRun.start_time.desc())
        )
        pipeline_summary: ReportPipelineSummary | None = None
        if pipeline_run:
            pipeline_summary = ReportPipelineSummary(
                pipeline_name=pipeline_run.pipeline_name,
                execution_status=pipeline_run.execution_status,
                quality_health=pipeline_run.quality_health,
                start_time=pipeline_run.start_time.isoformat(),
                end_time=pipeline_run.end_time.isoformat(),
                duration_ms=pipeline_run.duration_ms,
                records_ingested=pipeline_run.records_ingested,
                records_written=pipeline_run.records_written,
                error_message=pipeline_run.error_message,
            )

        # 6. Downstream blast radius tracing
        impacted_assets: list[ReportImpactedAsset] = []
        if first_failed_finding is not None:
            try:
                blast_report = ImpactAnalysisService.trace_impact(
                    target_id=first_failed_finding.id,
                    scenario_id=request.scenario_id,
                    db=db,
                )
                for asset in blast_report.affected_assets:
                    impacted_assets.append(
                        ReportImpactedAsset(
                            node_id=asset.node_id,
                            node_name=asset.name,
                            node_type=asset.type,
                            impact_status=str(asset.impact_status),
                            path=asset.dependency_path_names or asset.dependency_path,
                        )
                    )
            except Exception as e:
                logger.warning(
                    "Unable to compute blast radius for finding %s: %s",
                    first_failed_finding.id,
                    e,
                )

        # 7. Construct complete Report Model
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        now_dt = datetime.now(UTC)
        now_iso = now_dt.isoformat()

        report_title = request.title or investigation.title or f"Incident Report: {scenario.name}"

        # Determine overall quality health
        quality_health: str = "HEALTHY"
        if val_run.failed_checks > 0:
            quality_health = "CORRUPTED"
        elif val_run.warning_checks > 0:
            quality_health = "WARNING"

        report_data = IncidentReportData(
            report_id=report_id,
            investigation_id=investigation.id,
            generated_at=now_iso,
            title=report_title,
            scenario={
                "id": scenario.id,
                "name": scenario.name,
                "description": scenario.description,
                "category": scenario.category,
                "active_fixture_version": scenario.active_fixture_version,
            },
            investigation={
                "id": investigation.id,
                "status": investigation.status,
                "verified_facts": _safe_parse_str_list(investigation.verified_facts),
                "hypotheses": _safe_parse_str_list(investigation.hypotheses),
                "action_items": _safe_parse_str_list(investigation.action_items),
            },
            validation_summary=ReportValidationSummary(
                run_id=val_run.id,
                executed_at=val_run.executed_at.isoformat(),
                total_rules=val_run.total_checks,
                passed_count=val_run.passed_checks,
                failed_count=val_run.failed_checks,
                warning_count=val_run.warning_checks,
                quality_health=quality_health,
                duration_ms=val_run.execution_duration_ms,
            ),
            findings=finding_details,
            impacted_assets=impacted_assets,
            pipeline_summary=pipeline_summary,
            integrity={"sha256": ""},
        )

        # Calculate preliminary hash for report data
        data_dict = report_data.model_dump()
        prelim_json = json.dumps(data_dict, indent=2, sort_keys=True, default=str)
        content_hash = hashlib.sha256(prelim_json.encode("utf-8")).hexdigest()
        report_data.integrity["sha256"] = content_hash
        data_dict["integrity"]["sha256"] = content_hash

        # 8. Render JSON artifact
        json_content = json.dumps(data_dict, indent=2, default=str)
        json_hash = hashlib.sha256(json_content.encode("utf-8")).hexdigest()

        # 9. Render safe HTML artifact via Jinja2 autoescape
        env = cls.get_jinja_env()
        template = env.get_template("incident_report.html")
        html_content = template.render(**data_dict)
        html_hash = hashlib.sha256(html_content.encode("utf-8")).hexdigest()

        # 10. Write files to artifacts directory
        artifacts_dir = settings.artifacts_dir
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        json_file_path = (artifacts_dir / f"{report_id}.json").resolve()
        html_file_path = (artifacts_dir / f"{report_id}.html").resolve()

        json_file_path.write_text(json_content, encoding="utf-8")
        html_file_path.write_text(html_content, encoding="utf-8")

        # 11. Persist ReportArtifact records in SQLite
        json_artifact = ReportArtifact(
            id=f"{report_id}_json",
            investigation_id=investigation.id,
            scenario_id=scenario.id,
            validation_run_id=val_run.id,
            format=ReportFormat.JSON,
            file_path=str(json_file_path),
            sha256_hash=json_hash,
            file_size_bytes=len(json_content.encode("utf-8")),
            generated_at=now_dt,
        )

        html_artifact = ReportArtifact(
            id=f"{report_id}_html",
            investigation_id=investigation.id,
            scenario_id=scenario.id,
            validation_run_id=val_run.id,
            format=ReportFormat.HTML,
            file_path=str(html_file_path),
            sha256_hash=html_hash,
            file_size_bytes=len(html_content.encode("utf-8")),
            generated_at=now_dt,
        )

        db.add_all([json_artifact, html_artifact])
        db.commit()

        logger.info(
            "Generated report %s (JSON: %d bytes, HTML: %d bytes) for scenario %s",
            report_id,
            json_artifact.file_size_bytes,
            html_artifact.file_size_bytes,
            scenario.id,
        )

        return ReportGenerateResponse(
            report_id=report_id,
            investigation_id=investigation.id,
            generated_at=now_dt,
            json_url=f"/api/v1/reports/{report_id}/export?format=json",
            html_url=f"/api/v1/reports/{report_id}/export?format=html",
        )

    @classmethod
    def get_report_artifact(
        cls,
        db: Session,
        report_id: str,
        export_format: str | ReportFormat,
    ) -> tuple[ReportArtifact, Path]:
        """Retrieve a specific report artifact and verify path containment.

        Args:
            db: Active SQLAlchemy database session.
            report_id: Report identifier, artifact identifier, or investigation ID.
            export_format: Desired format ('json' or 'html').

        Returns:
            Tuple of (ReportArtifact model, resolved Path on disk).

        Raises:
            LuxException: If export_format is invalid.
            NotFoundError: If artifact or file on disk is not found.
        """
        fmt_str = str(export_format).lower().strip()
        if fmt_str not in ("json", "html"):
            raise LuxException(
                code="INVALID_REPORT_FORMAT",
                message=f"Unsupported report format '{export_format}'. Expected 'json' or 'html'.",
                details={"format": export_format},
            )

        # Lookup artifact by ID combinations
        artifact = db.scalar(
            select(ReportArtifact).where(
                (ReportArtifact.id == f"{report_id}_{fmt_str}")
                | (ReportArtifact.id == f"{report_id}-{fmt_str}")
                | ((ReportArtifact.id == report_id) & (ReportArtifact.format == fmt_str))
            )
        )

        if not artifact:
            # Try investigation_id lookup
            artifact = db.scalar(
                select(ReportArtifact).where(
                    (ReportArtifact.investigation_id == report_id)
                    & (ReportArtifact.format == fmt_str)
                )
            )

        if not artifact:
            raise NotFoundError(
                code="REPORT_NOT_FOUND",
                message=f"Report artifact '{report_id}' with format '{fmt_str}' was not found.",
                details={"report_id": report_id, "format": fmt_str},
            )

        target_path = Path(artifact.file_path).resolve()
        artifacts_dir = settings.artifacts_dir.resolve()

        # Path traversal guard
        if not target_path.is_relative_to(artifacts_dir):
            logger.error(
                "Path traversal attempt detected for artifact %s: %s",
                artifact.id,
                target_path,
            )
            raise LuxException(
                code="PATH_TRAVERSAL_DETECTED",
                message="Report file path resolves outside authorized storage directory.",
                details={"report_id": report_id},
            )

        if not target_path.exists():
            raise NotFoundError(
                code="REPORT_FILE_NOT_FOUND",
                message=f"Report file on disk was not found for artifact '{artifact.id}'.",
                details={"report_id": report_id, "file_path": str(target_path)},
            )

        return artifact, target_path

    @classmethod
    def list_artifacts(
        cls,
        db: Session,
        scenario_id: str | None = None,
        investigation_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReportArtifact], int]:
        """List generated report artifacts with optional filtering."""
        query = select(ReportArtifact)
        count_query = select(func.count(ReportArtifact.id))

        if scenario_id:
            query = query.where(ReportArtifact.scenario_id == scenario_id)
            count_query = count_query.where(ReportArtifact.scenario_id == scenario_id)

        if investigation_id:
            query = query.where(ReportArtifact.investigation_id == investigation_id)
            count_query = count_query.where(ReportArtifact.investigation_id == investigation_id)

        total = db.scalar(count_query) or 0
        items = list(
            db.scalars(
                query.order_by(ReportArtifact.generated_at.desc()).offset(offset).limit(limit)
            ).all()
        )
        return items, total
