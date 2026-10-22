"""Recovery verification service swapping fixtures, re-validating, and assessing asset recovery."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import LuxException, NotFoundError
from app.models.dataset import Dataset
from app.models.pipeline import FreshnessCheck, PipelineRun
from app.models.scenario import Scenario
from app.models.validation import ValidationFinding, ValidationRule, ValidationRun
from app.schemas.impact import AssetImpactStatus
from app.schemas.recovery import (
    RecoveryComparison,
    RecoveryRunSummary,
    RecoveryVerifyResponse,
    ResolvedFindingItem,
)
from app.services.impact.analyzer import ImpactAnalysisService
from app.services.ingestion.reader import DatasetReader
from app.services.lineage.graph import LineageGraph
from app.services.pipeline.freshness import FreshnessService
from app.services.pipeline.service import PipelineHistoryService
from app.services.validation.runner import ValidationRunnerService

logger = logging.getLogger("lux.services.validation.recovery")


class RecoveryService:
    """Service orchestrating recovery verification across datasets, validations, and lineage."""

    @classmethod
    def _load_lineage_graph(cls, scenario_id: str, db: Session) -> LineageGraph:
        """Load LineageGraph instance from SQLite or scenario metadata on disk."""
        try:
            return LineageGraph.from_db(db, scenario_id=scenario_id)
        except NotFoundError:
            pass
        except Exception as exc:
            logger.warning(
                "Could not load LineageGraph from DB for scenario '%s': %s", scenario_id, exc
            )

        scenario_file = settings.scenarios_dir / scenario_id / "scenario.json"
        if scenario_file.exists():
            return LineageGraph.from_scenario_file(scenario_file, scenario_id=scenario_id)

        raise NotFoundError(
            code="SCENARIO_NOT_FOUND",
            message=(
                f"Lineage graph for scenario '{scenario_id}' was not found in DB or filesystem."
            ),
            details={"scenario_id": scenario_id},
        )

    @classmethod
    def swap_fixtures(
        cls,
        scenario_id: str,
        fixture_version: str,
        db: Session,
    ) -> None:
        """Swap dataset files and pipeline history to target fixture version safely.

        Args:
            scenario_id: Scenario identifier.
            fixture_version: 'defective' or 'corrected'.
            db: Active SQLAlchemy database session.

        Raises:
            NotFoundError: If scenario or fixture files are not found.
            LuxException: If fixture version is invalid.
        """
        if fixture_version not in ("defective", "corrected"):
            raise LuxException(
                code="INVALID_FIXTURE_VERSION",
                message=(
                    f"Invalid fixture version '{fixture_version}'. "
                    "Must be 'defective' or 'corrected'."
                ),
                details={"fixture_version": fixture_version},
            )

        scenario = db.execute(
            select(Scenario).where(Scenario.id == scenario_id)
        ).scalar_one_or_none()
        if not scenario:
            raise NotFoundError(
                code="SCENARIO_NOT_FOUND",
                message=f"Scenario '{scenario_id}' was not found in database.",
                details={"scenario_id": scenario_id},
            )

        scenario_dir = settings.scenarios_dir / scenario_id
        scenario_json_path = scenario_dir / "scenario.json"
        if not scenario_json_path.exists():
            raise NotFoundError(
                code="SCENARIO_NOT_FOUND",
                message=f"Scenario definition file not found at {scenario_json_path}.",
                details={"scenario_id": scenario_id, "file_path": str(scenario_json_path)},
            )

        with open(scenario_json_path, encoding="utf-8") as f:
            scenario_meta: dict[str, Any] = json.load(f)

        now = datetime.now(UTC)
        loaded_datasets: list[str] = []

        # 1. Update registered dataset file paths and re-inspect record counts
        for dataset_def in scenario_meta.get("datasets", []):
            d_id = dataset_def["id"]
            d_name = dataset_def.get("name", f"{d_id}.csv")
            d_format = dataset_def.get("format", "csv").lower()

            subpath = dataset_def.get(f"{fixture_version}_path") or f"{fixture_version}/{d_name}"
            fixture_file = (scenario_dir / subpath).resolve()
            if not fixture_file.exists():
                raise NotFoundError(
                    code="FIXTURE_FILE_NOT_FOUND",
                    message=f"Fixture file '{subpath}' not found for dataset '{d_id}'.",
                    details={"dataset_id": d_id, "path": str(fixture_file)},
                )

            record_count, columns, schemas = DatasetReader.inspect_file(fixture_file, d_format)
            file_size_bytes = fixture_file.stat().st_size
            schema_json = json.dumps([s.model_dump() for s in schemas])

            dataset = db.execute(
                select(Dataset).where(Dataset.id == d_id, Dataset.scenario_id == scenario_id)
            ).scalar_one_or_none()

            if dataset:
                dataset.file_path = str(fixture_file)
                dataset.file_size_bytes = file_size_bytes
                dataset.record_count = record_count
                dataset.column_count = len(columns)
                dataset.schema_definition = schema_json
                loaded_datasets.append(d_id)

        # 2. Update scenario active fixture version
        scenario.active_fixture_version = fixture_version
        scenario.updated_at = now

        # 3. Reload pipeline runs & freshness checks if fixture-specific pipeline history exists
        pipeline_history_path = scenario_dir / "pipeline_history.json"
        if fixture_version == "corrected":
            corrected_pipe = scenario_dir / "corrected" / "pipeline_history.json"
            if corrected_pipe.exists():
                pipeline_history_path = corrected_pipe

        if pipeline_history_path.exists():
            with open(pipeline_history_path, encoding="utf-8") as pf:
                pipeline_meta = json.load(pf)

            db.execute(delete(FreshnessCheck).where(FreshnessCheck.scenario_id == scenario_id))
            db.execute(delete(PipelineRun).where(PipelineRun.scenario_id == scenario_id))

            PipelineHistoryService.seed_pipeline_runs(
                db=db,
                scenario_id=scenario_id,
                runs_data=pipeline_meta.get("pipeline_runs", []),
            )
            FreshnessService.seed_freshness_checks(
                db=db,
                scenario_id=scenario_id,
                checks_data=pipeline_meta.get("freshness_checks", []),
                loaded_datasets=loaded_datasets,
            )

        db.commit()
        logger.info(
            "Scenario '%s' successfully swapped to fixture version '%s'.",
            scenario_id,
            fixture_version,
        )

    @classmethod
    def verify_recovery(
        cls,
        scenario_id: str,
        db: Session,
        target_fixture_version: str = "corrected",
    ) -> RecoveryVerifyResponse:
        """Execute recovery verification by swapping fixtures, re-validating, and diffing."""
        # 1. Verify scenario existence
        scenario = db.execute(
            select(Scenario).where(Scenario.id == scenario_id)
        ).scalar_one_or_none()
        if not scenario:
            raise NotFoundError(
                code="SCENARIO_NOT_FOUND",
                message=(
                    f"Scenario '{scenario_id}' was not found in database. Please load it first."
                ),
                details={"scenario_id": scenario_id},
            )

        # 2. Identify baseline previous validation run (prefer latest defective run)
        previous_run = (
            db.execute(
                select(ValidationRun)
                .where(
                    ValidationRun.scenario_id == scenario_id,
                    ValidationRun.fixture_version == "defective",
                )
                .order_by(ValidationRun.executed_at.desc())
            )
            .scalars()
            .first()
        )

        if not previous_run:
            # If no defective run found, check if there's any previous run with a different version
            any_previous = (
                db.execute(
                    select(ValidationRun)
                    .where(ValidationRun.scenario_id == scenario_id)
                    .order_by(ValidationRun.executed_at.desc())
                )
                .scalars()
                .first()
            )

            if any_previous and any_previous.fixture_version != target_fixture_version:
                previous_run = any_previous
            else:
                # If currently in defective mode, execute baseline run first
                if scenario.active_fixture_version == "defective":
                    previous_run = ValidationRunnerService.execute_validation_run(scenario_id, db)
                elif any_previous:
                    previous_run = any_previous
                else:
                    previous_run = ValidationRunnerService.execute_validation_run(scenario_id, db)

        # Retrieve previous findings and compute its quality health status
        prev_findings = (
            db.execute(
                select(ValidationFinding)
                .where(ValidationFinding.run_id == previous_run.id)
                .order_by(ValidationFinding.created_at.asc())
            )
            .scalars()
            .all()
        )
        prev_quality_health = PipelineHistoryService.evaluate_quality_health(
            prev_findings, previous_run.total_checks
        ).value

        # 3. Swap dataset fixtures and pipeline records to clean version
        cls.swap_fixtures(
            scenario_id=scenario_id,
            fixture_version=target_fixture_version,
            db=db,
        )

        # 4. Re-execute validation rules against clean data
        current_run = ValidationRunnerService.execute_validation_run(scenario_id, db)
        current_findings = (
            db.execute(
                select(ValidationFinding)
                .where(ValidationFinding.run_id == current_run.id)
                .order_by(ValidationFinding.created_at.asc())
            )
            .scalars()
            .all()
        )
        current_quality_health = PipelineHistoryService.evaluate_quality_health(
            current_findings, current_run.total_checks
        ).value

        # 5. Fetch rules to enrich findings with human-readable names and preserve declaration order
        rules = (
            db.execute(
                select(ValidationRule)
                .where(ValidationRule.scenario_id == scenario_id)
                .order_by(ValidationRule.dataset_id, ValidationRule.id)
            )
            .scalars()
            .all()
        )
        rules_map = {r.id: r for r in rules}

        # 6. Diffs: compare previously failed checks to current run outcomes
        current_findings_by_rule = {f.rule_id: f for f in current_findings}
        prev_failed_findings = [
            f for f in prev_findings if str(f.status).upper() in ("FAILED", "ERROR")
        ]

        resolved_items: list[ResolvedFindingItem] = []
        for prev_f in prev_failed_findings:
            curr_f = current_findings_by_rule.get(prev_f.rule_id)
            rule = rules_map.get(prev_f.rule_id)
            rule_name = rule.name if rule else prev_f.rule_id

            if curr_f and str(curr_f.status).upper() == "PASSED":
                resolution_status = "RESOLVED"
            else:
                resolution_status = "UNRESOLVED"

            resolved_items.append(
                ResolvedFindingItem(
                    rule_id=prev_f.rule_id,
                    rule_name=rule_name,
                    status=resolution_status,
                    severity=prev_f.severity,
                    category=prev_f.rule_category,
                    dataset_id=prev_f.dataset_id,
                    previous_status=prev_f.status,
                    current_status=curr_f.status if curr_f else None,
                    message=curr_f.message if curr_f else None,
                )
            )

        # 7. Evaluate downstream recovery across the Lineage Graph
        lineage_graph = cls._load_lineage_graph(scenario_id, db)
        curr_failed = [f for f in current_findings if str(f.status).upper() in ("FAILED", "ERROR")]
        failed_dataset_ids = {f.dataset_id for f in curr_failed if f.dataset_id}

        failed_root_nodes: set[str] = set()
        for ds_id in failed_dataset_ids:
            for nid in lineage_graph.nodes:
                ndata = lineage_graph.get_node(nid)
                if ndata.get("dataset_id") == ds_id:
                    failed_root_nodes.add(nid)

        classifications = ImpactAnalysisService.classify_graph_nodes(
            lineage_graph, failed_root_nodes
        )
        all_downstream_healthy = all(
            tier == AssetImpactStatus.HEALTHY for tier in classifications.values()
        )

        if all_downstream_healthy and current_run.failed_checks == 0:
            downstream_status = "ALL_ASSETS_HEALTHY"
        elif any(item.status == "RESOLVED" for item in resolved_items):
            downstream_status = "PARTIALLY_RECOVERED"
        else:
            downstream_status = "RECOVERY_FAILED"

        return RecoveryVerifyResponse(
            scenario_id=scenario_id,
            comparison=RecoveryComparison(
                previous_run=RecoveryRunSummary(
                    run_id=previous_run.id,
                    fixture_version=previous_run.fixture_version,
                    failed_checks=previous_run.failed_checks,
                    quality_health=prev_quality_health,
                    total_checks=previous_run.total_checks,
                    passed_checks=previous_run.passed_checks,
                    execution_duration_ms=previous_run.execution_duration_ms,
                    executed_at=previous_run.executed_at,
                ),
                current_run=RecoveryRunSummary(
                    run_id=current_run.id,
                    fixture_version=current_run.fixture_version,
                    failed_checks=current_run.failed_checks,
                    quality_health=current_quality_health,
                    total_checks=current_run.total_checks,
                    passed_checks=current_run.passed_checks,
                    execution_duration_ms=current_run.execution_duration_ms,
                    executed_at=current_run.executed_at,
                ),
                resolved_findings=resolved_items,
                downstream_recovery_status=downstream_status,
            ),
        )
