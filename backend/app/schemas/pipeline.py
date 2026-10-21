"""Pydantic schemas and enums for pipeline run history and dual-dimension status tracking."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("lux.schemas.pipeline")


class PipelineExecutionStatus(StrEnum):
    """Compute execution dimension status tracking process termination outcome."""

    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    RUNNING = "RUNNING"
    CANCELLED = "CANCELLED"


class QualityHealthStatus(StrEnum):
    """Data quality dimension status tracking data integrity from validation checks."""

    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DEGRADED = "DEGRADED"
    CORRUPTED = "CORRUPTED"
    UNVALIDATED = "UNVALIDATED"


class PipelineStepLog(BaseModel):
    """Execution step log details within a pipeline run."""

    step: str = Field(..., description="Step name or identifier")
    status: str = Field(..., description="Step outcome status (e.g. SUCCESS, FAILED)")
    records: int = Field(default=0, description="Records processed during this step")
    duration_ms: int = Field(default=0, description="Step duration in milliseconds")


class PipelineRunResponse(BaseModel):
    """Pipeline execution run response reflecting dual compute and data quality status."""

    id: str = Field(..., description="Unique pipeline run identifier")
    scenario_id: str = Field(..., description="Associated scenario identifier")
    pipeline_name: str = Field(..., description="Name of the pipeline")
    execution_status: str = Field(..., description="Compute execution dimension status")
    quality_health: str = Field(..., description="Data quality dimension status")
    start_time: datetime = Field(..., description="Pipeline execution start timestamp")
    end_time: datetime = Field(..., description="Pipeline execution end timestamp")
    duration_ms: int = Field(..., description="Execution duration in milliseconds")
    records_ingested: int = Field(default=0, description="Total records ingested")
    records_written: int = Field(default=0, description="Total records written")
    error_message: str | None = Field(default=None, description="Error message if run failed")
    run_log: list[PipelineStepLog] = Field(
        default_factory=list, description="Step-level execution logs"
    )
    created_at: datetime | None = Field(
        default=None, description="Timestamp when record was created"
    )

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, model: Any, include_logs: bool = True) -> PipelineRunResponse:
        """Construct schema from SQLAlchemy PipelineRun model handling JSON run_log."""
        parsed_logs: list[PipelineStepLog] = []
        if include_logs and getattr(model, "run_log", None):
            raw_log = model.run_log
            if isinstance(raw_log, str):
                try:
                    data = json.loads(raw_log)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                parsed_logs.append(
                                    PipelineStepLog(
                                        step=str(item.get("step", "")),
                                        status=str(item.get("status", "SUCCESS")),
                                        records=int(item.get("records", 0)),
                                        duration_ms=int(item.get("duration_ms", 0)),
                                    )
                                )
                            elif isinstance(item, str):
                                parsed_logs.append(
                                    PipelineStepLog(
                                        step=item,
                                        status="SUCCESS",
                                        records=0,
                                        duration_ms=0,
                                    )
                                )
                except (json.JSONDecodeError, TypeError) as exc:
                    logger.warning("Failed to parse run_log JSON for run %s: %s", model.id, exc)
            elif isinstance(raw_log, list):
                for item in raw_log:
                    if isinstance(item, dict):
                        parsed_logs.append(
                            PipelineStepLog(
                                step=str(item.get("step", "")),
                                status=str(item.get("status", "SUCCESS")),
                                records=int(item.get("records", 0)),
                                duration_ms=int(item.get("duration_ms", 0)),
                            )
                        )
                    elif isinstance(item, str):
                        parsed_logs.append(
                            PipelineStepLog(
                                step=item,
                                status="SUCCESS",
                                records=0,
                                duration_ms=0,
                            )
                        )

        return cls(
            id=model.id,
            scenario_id=model.scenario_id,
            pipeline_name=model.pipeline_name,
            execution_status=model.execution_status,
            quality_health=model.quality_health,
            start_time=model.start_time,
            end_time=model.end_time,
            duration_ms=model.duration_ms,
            records_ingested=model.records_ingested,
            records_written=model.records_written,
            error_message=model.error_message,
            run_log=parsed_logs,
            created_at=getattr(model, "created_at", None),
        )

