"""Pydantic schemas and enums for incident investigation workspace."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("lux.schemas.investigation")


class InvestigationStatus(StrEnum):
    """Investigation lifecycle status."""

    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    RECOVERED = "RECOVERED"
    CLOSED = "CLOSED"


class InvestigationItemType(StrEnum):
    """Explicit item classification separating verified facts from working theories."""

    VERIFIED_FACT = "VERIFIED_FACT"
    HYPOTHESIS = "HYPOTHESIS"
    ACTION_ITEM = "ACTION_ITEM"


class InvestigationItem(BaseModel):
    """A typed item within an investigation workspace enforcing item category boundaries."""

    item_type: InvestigationItemType = Field(
        ..., description="Classification category (fact, hypothesis, or action item)"
    )
    content: str = Field(..., min_length=1, description="Textual description of the item")
    source: str | None = Field(
        default=None,
        description="Optional origin source (e.g. 'VAL-ORD-001', 'pipeline_log', 'engineer')",
    )


class InvestigationCreateRequest(BaseModel):
    """Request payload to create a new investigation workspace."""

    scenario_id: str = Field(..., description="Target scenario identifier")
    title: str = Field(..., min_length=1, description="Human-readable investigation title")
    status: InvestigationStatus | str = Field(
        default=InvestigationStatus.OPEN, description="Initial investigation status"
    )
    initial_finding_id: str | None = Field(
        default=None, description="Optional validation finding ID that triggered the investigation"
    )
    verified_facts: list[str] = Field(
        default_factory=list,
        description="Observable, confirmed facts from validation findings or logs",
    )
    hypotheses: list[str] = Field(
        default_factory=list,
        description="Working theories or unconfirmed assumptions regarding root causes",
    )
    action_items: list[str] = Field(
        default_factory=list,
        description="Remediation steps or follow-up tasks to resolve the incident",
    )


class InvestigationUpdateRequest(BaseModel):
    """Request payload to partially update an existing investigation workspace."""

    title: str | None = Field(default=None, description="Updated investigation title")
    status: InvestigationStatus | str | None = Field(
        default=None, description="Updated investigation lifecycle status"
    )
    initial_finding_id: str | None = Field(
        default=None, description="Associated initial finding ID"
    )
    verified_facts: list[str] | None = Field(
        default=None, description="Updated list of verified facts"
    )
    hypotheses: list[str] | None = Field(
        default=None, description="Updated list of working hypotheses"
    )
    action_items: list[str] | None = Field(
        default=None, description="Updated list of remediation action items"
    )


class InvestigationSynthesizeRequest(BaseModel):
    """Payload to automatically synthesize an investigation workspace from scenario evidence."""

    scenario_id: str = Field(..., description="Scenario identifier to inspect")
    title: str | None = Field(
        default=None, description="Optional custom title (defaults to scenario-based title)"
    )
    finding_id: str | None = Field(
        default=None, description="Optional specific finding ID to focus the investigation around"
    )


def _safe_parse_str_list(value: Any, default: list[str] | None = None) -> list[str]:
    """Parse JSON string or sequence into a list of strings cleanly."""
    if default is None:
        default = []
    if value is None:
        return default
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        val_str = value.strip()
        if not val_str:
            return default
        try:
            parsed = json.loads(val_str)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
            return [str(parsed)]
        except (json.JSONDecodeError, TypeError):
            return [val_str]
    return default


class InvestigationResponse(BaseModel):
    """Full representation of an investigation workspace."""

    id: str = Field(..., description="Unique investigation identifier (e.g. inv_12345678)")
    scenario_id: str = Field(..., description="Associated scenario identifier")
    title: str = Field(..., description="Investigation workspace title")
    status: str = Field(..., description="Current investigation status")
    initial_finding_id: str | None = Field(
        default=None, description="Initial validation finding identifier"
    )
    verified_facts: list[str] = Field(
        default_factory=list,
        description="Verified observable facts (cannot be conflated with hypotheses)",
    )
    hypotheses: list[str] = Field(
        default_factory=list,
        description="Working hypotheses and theories regarding root cause",
    )
    action_items: list[str] = Field(
        default_factory=list,
        description="Concrete remediation actions and follow-up items",
    )
    created_at: datetime = Field(..., description="Timestamp when investigation was created")
    updated_at: datetime = Field(..., description="Timestamp when investigation was last updated")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, model: Any) -> InvestigationResponse:
        """Construct response schema from SQLAlchemy Investigation model handling JSON fields."""
        return cls(
            id=model.id,
            scenario_id=model.scenario_id,
            title=model.title,
            status=model.status,
            initial_finding_id=model.initial_finding_id,
            verified_facts=_safe_parse_str_list(getattr(model, "verified_facts", "[]")),
            hypotheses=_safe_parse_str_list(getattr(model, "hypotheses", "[]")),
            action_items=_safe_parse_str_list(getattr(model, "action_items", "[]")),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class InvestigationListResponse(BaseModel):
    """List response of investigations."""

    total: int = Field(..., description="Total count of investigations matching query")
    items: list[InvestigationResponse] = Field(
        default_factory=list, description="List of investigations"
    )
