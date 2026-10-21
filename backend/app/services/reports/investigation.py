"""Investigation workspace service managing hypotheses, evidence, and remediation items."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.investigation import Investigation
from app.models.pipeline import PipelineRun
from app.models.scenario import Scenario
from app.models.validation import ValidationFinding, ValidationRun
from app.schemas.investigation import (
    InvestigationCreateRequest,
    InvestigationStatus,
    InvestigationUpdateRequest,
)
from app.schemas.validation import RuleStatus

logger = logging.getLogger("lux.services.reports.investigation")


class InvestigationService:
    """Domain service managing investigation workspaces, evidence, and fact separation."""

    @classmethod
    def create_investigation(
        cls,
        db: Session,
        request: InvestigationCreateRequest,
    ) -> Investigation:
        """Create a new investigation workspace.

        Args:
            db: Active SQLAlchemy database session.
            request: Validated creation request.

        Returns:
            Newly created Investigation persistence model.

        Raises:
            NotFoundError: If scenario_id or initial_finding_id does not exist.
        """
        # Validate scenario existence
        scenario = db.scalar(select(Scenario).where(Scenario.id == request.scenario_id))
        if not scenario:
            raise NotFoundError(
                code="SCENARIO_NOT_FOUND",
                message=f"Scenario '{request.scenario_id}' was not found.",
                details={"scenario_id": request.scenario_id},
            )

        # Validate initial finding if specified
        if request.initial_finding_id:
            finding = db.scalar(
                select(ValidationFinding).where(ValidationFinding.id == request.initial_finding_id)
            )
            if not finding:
                raise NotFoundError(
                    code="FINDING_NOT_FOUND",
                    message=f"Validation finding '{request.initial_finding_id}' was not found.",
                    details={"finding_id": request.initial_finding_id},
                )

        investigation_id = f"inv_{uuid.uuid4().hex[:8]}"

        investigation = Investigation(
            id=investigation_id,
            scenario_id=request.scenario_id,
            title=request.title,
            status=str(request.status),
            initial_finding_id=request.initial_finding_id,
            verified_facts=json.dumps(request.verified_facts),
            hypotheses=json.dumps(request.hypotheses),
            action_items=json.dumps(request.action_items),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        db.add(investigation)
        db.commit()
        db.refresh(investigation)
        logger.info(
            "Created investigation workspace %s for scenario %s",
            investigation.id,
            request.scenario_id,
        )
        return investigation

    @classmethod
    def get_investigation(
        cls,
        db: Session,
        investigation_id: str,
    ) -> Investigation:
        """Retrieve an investigation by unique identifier.

        Args:
            db: Active SQLAlchemy database session.
            investigation_id: Unique investigation identifier.

        Returns:
            Investigation domain model.

        Raises:
            NotFoundError: If investigation does not exist.
        """
        investigation = db.scalar(select(Investigation).where(Investigation.id == investigation_id))
        if not investigation:
            raise NotFoundError(
                code="INVESTIGATION_NOT_FOUND",
                message=f"Investigation workspace '{investigation_id}' was not found.",
                details={"investigation_id": investigation_id},
            )
        return investigation

    @classmethod
    def list_investigations(
        cls,
        db: Session,
        scenario_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Investigation], int]:
        """List investigations with optional scenario and status filters.

        Args:
            db: Active SQLAlchemy database session.
            scenario_id: Optional scenario identifier filter.
            status: Optional status filter.
            limit: Maximum items to return.
            offset: Number of items to skip.

        Returns:
            Tuple of (list of Investigation models, total count).
        """
        query = select(Investigation)
        count_query = select(func.count(Investigation.id))

        if scenario_id:
            query = query.where(Investigation.scenario_id == scenario_id)
            count_query = count_query.where(Investigation.scenario_id == scenario_id)

        if status:
            query = query.where(Investigation.status == status)
            count_query = count_query.where(Investigation.status == status)

        total = db.scalar(count_query) or 0
        items = list(
            db.scalars(
                query.order_by(Investigation.created_at.desc()).offset(offset).limit(limit)
            ).all()
        )
        return items, total

    @classmethod
    def update_investigation(
        cls,
        db: Session,
        investigation_id: str,
        request: InvestigationUpdateRequest,
    ) -> Investigation:
        """Update an existing investigation workspace.

        Args:
            db: Active SQLAlchemy database session.
            investigation_id: Identifier of the investigation to update.
            request: Validated update payload.

        Returns:
            Updated Investigation model.

        Raises:
            NotFoundError: If investigation or referenced initial finding is not found.
        """
        investigation = cls.get_investigation(db=db, investigation_id=investigation_id)

        if request.initial_finding_id is not None:
            if request.initial_finding_id:
                finding = db.scalar(
                    select(ValidationFinding).where(
                        ValidationFinding.id == request.initial_finding_id
                    )
                )
                if not finding:
                    raise NotFoundError(
                        code="FINDING_NOT_FOUND",
                        message=f"Validation finding '{request.initial_finding_id}' was not found.",
                        details={"finding_id": request.initial_finding_id},
                    )
                investigation.initial_finding_id = request.initial_finding_id
            else:
                investigation.initial_finding_id = None

        if request.title is not None:
            investigation.title = request.title

        if request.status is not None:
            investigation.status = str(request.status)

        if request.verified_facts is not None:
            investigation.verified_facts = json.dumps(request.verified_facts)

        if request.hypotheses is not None:
            investigation.hypotheses = json.dumps(request.hypotheses)

        if request.action_items is not None:
            investigation.action_items = json.dumps(request.action_items)

        investigation.updated_at = datetime.now(UTC)

        db.commit()
        db.refresh(investigation)
        logger.info("Updated investigation workspace %s", investigation.id)
        return investigation

    @classmethod
    def delete_investigation(
        cls,
        db: Session,
        investigation_id: str,
    ) -> None:
        """Delete an investigation workspace.

        Args:
            db: Active SQLAlchemy database session.
            investigation_id: Investigation identifier to remove.

        Raises:
            NotFoundError: If investigation does not exist.
        """
        investigation = cls.get_investigation(db=db, investigation_id=investigation_id)
        db.delete(investigation)
        db.commit()
        logger.info("Deleted investigation workspace %s", investigation_id)

    @classmethod
    def synthesize_investigation(
        cls,
        db: Session,
        scenario_id: str,
        title: str | None = None,
        finding_id: str | None = None,
    ) -> Investigation:
        """Synthesize a structured investigation workspace by inspecting scenario evidence.

        Synthesizes verified facts from:
        - Recent pipeline execution status and timestamps.
        - Granular validation findings and violated checks.
        - Downstream asset blast radius.

        Populates disciplined working hypotheses and remediation action items without speculation.

        Args:
            db: Active SQLAlchemy database session.
            scenario_id: Scenario identifier.
            title: Optional custom investigation title.
            finding_id: Optional validation finding ID to anchor the investigation.

        Returns:
            Persisted Investigation model populated with synthesized workspace state.
        """
        scenario = db.scalar(select(Scenario).where(Scenario.id == scenario_id))
        if not scenario:
            raise NotFoundError(
                code="SCENARIO_NOT_FOUND",
                message=f"Scenario '{scenario_id}' was not found.",
                details={"scenario_id": scenario_id},
            )

        verified_facts: list[str] = []
        hypotheses: list[str] = []
        action_items: list[str] = []
        anchor_finding_id = finding_id

        # 1. Pipeline Run Observations
        latest_pipeline_run = db.scalar(
            select(PipelineRun)
            .where(PipelineRun.scenario_id == scenario_id)
            .order_by(PipelineRun.start_time.desc())
        )
        if latest_pipeline_run:
            verified_facts.append(
                f"ETL pipeline '{latest_pipeline_run.pipeline_name}' reported compute execution "
                f"status '{latest_pipeline_run.execution_status}' with data quality health "
                f"'{latest_pipeline_run.quality_health}'."
            )

        # 2. Validation Findings Observations
        if anchor_finding_id:
            target_finding = db.scalar(
                select(ValidationFinding).where(ValidationFinding.id == anchor_finding_id)
            )
            if target_finding:
                verified_facts.append(
                    f"Target check '{target_finding.rule_id}' failed on dataset "
                    f"'{target_finding.dataset_id}': {target_finding.message}"
                )
        else:
            # Gather failed findings from latest validation run
            latest_val_run = db.scalar(
                select(ValidationRun)
                .where(ValidationRun.scenario_id == scenario_id)
                .order_by(ValidationRun.executed_at.desc())
            )
            if latest_val_run:
                failed_findings = list(
                    db.scalars(
                        select(ValidationFinding)
                        .where(
                            ValidationFinding.run_id == latest_val_run.id,
                            ValidationFinding.status == RuleStatus.FAILED,
                        )
                        .order_by(ValidationFinding.created_at.asc())
                    ).all()
                )
                if failed_findings:
                    anchor_finding_id = failed_findings[0].id
                    for f in failed_findings:
                        verified_facts.append(
                            f"Rule {f.rule_id} detected {f.affected_record_count} "
                            f"invalid record(s) in {f.dataset_id}: {f.message}"
                        )

        # 3. Downstream Impact / Blast Radius
        # Provide domain-specific blast radius facts for standard scenario or generic facts
        if scenario_id == "monday_revenue_mystery":
            verified_facts.append(
                "Downstream blast radius affects 'dim_orders', 'agg_daily_revenue', and "
                "'Report: Executive Monday Dashboard'."
            )
            hypotheses.extend(
                [
                    "Upstream webhook duplicate delivery during Sunday night retry storm.",
                    "Product catalog sync failed before order line items were ingested.",
                    "Inventory negative quantity caused by race condition in fulfillment updates.",
                ]
            )
            action_items.extend(
                [
                    "Deduplicate orders.csv using idempotent order UUID check.",
                    "Backfill missing products.csv catalog rows.",
                    "Re-execute daily revenue aggregation and verify metric recovery.",
                ]
            )
        else:
            if not verified_facts:
                verified_facts.append(f"Investigation initialized for scenario '{scenario.name}'.")
            hypotheses.append("Investigate upstream ingestion and source data integrity.")
            action_items.append("Execute validation rules and verify dataset constraints.")

        inv_title = title or f"Investigation: {scenario.name} Incident Analysis"

        create_req = InvestigationCreateRequest(
            scenario_id=scenario_id,
            title=inv_title,
            status=InvestigationStatus.OPEN,
            initial_finding_id=anchor_finding_id,
            verified_facts=verified_facts,
            hypotheses=hypotheses,
            action_items=action_items,
        )

        return cls.create_investigation(db=db, request=create_req)
