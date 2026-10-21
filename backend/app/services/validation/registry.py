"""Rule registry for dynamic registration and instantiation of validation rule evaluators."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from app.core.errors import LuxException
from app.schemas.validation import RuleCategory, RuleSeverity, ValidationRuleConfig
from app.services.validation.base import BaseValidationRule
from app.services.validation.core import (
    NullCheckRule,
    RecordCountRule,
    TypeValidityRule,
    UniquenessRule,
    ValueRangeRule,
)
from app.services.validation.relational import (
    FreshnessRule,
    ReferentialIntegrityRule,
    SchemaIntegrityRule,
    TemporalAnomalyRule,
)


class RuleRegistry:
    """Registry maintaining mappings from rule categories to evaluator implementations."""

    _registry: dict[str, type[BaseValidationRule]] = {}

    @classmethod
    def register(cls, category: RuleCategory | str, rule_cls: type[BaseValidationRule]) -> None:
        """Register a rule evaluator class for a category."""
        key = category.value if isinstance(category, RuleCategory) else str(category).upper()
        cls._registry[key] = rule_cls

    @classmethod
    def register_rule(
        cls, category: RuleCategory | str
    ) -> Callable[[type[BaseValidationRule]], type[BaseValidationRule]]:
        """Decorator to register a rule evaluator class."""

        def decorator(subclass: type[BaseValidationRule]) -> type[BaseValidationRule]:
            cls.register(category, subclass)
            return subclass

        return decorator

    @classmethod
    def get_rule_class(cls, category: RuleCategory | str) -> type[BaseValidationRule] | None:
        """Retrieve registered rule class for category if present."""
        key = category.value if isinstance(category, RuleCategory) else str(category).upper()
        return cls._registry.get(key)

    @classmethod
    def is_registered(cls, category: RuleCategory | str) -> bool:
        """Check whether category is registered."""
        key = category.value if isinstance(category, RuleCategory) else str(category).upper()
        return key in cls._registry

    @classmethod
    def list_registered_categories(cls) -> list[str]:
        """Return list of all registered rule category names."""
        return sorted(cls._registry.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered rules (useful for testing)."""
        cls._registry.clear()

    @classmethod
    def create_rule(cls, config: dict[str, Any] | ValidationRuleConfig | Any) -> BaseValidationRule:
        """Instantiate a rule evaluator from dictionary, Pydantic schema, or SQLAlchemy model."""
        params: Any
        if isinstance(config, ValidationRuleConfig):
            rule_id = config.id
            name = config.name
            dataset_id = config.dataset_id
            category_raw = config.category
            severity_raw = config.severity
            params = config.parameters
            description = config.description
            is_active = config.is_active
        elif isinstance(config, dict):
            rule_id = str(config.get("id") or config.get("rule_id", ""))
            name = str(config.get("name") or rule_id)
            dataset_id = str(config.get("dataset_id", ""))
            category_raw = config.get("category", "")
            severity_raw = config.get("severity", RuleSeverity.HIGH)
            params = config.get("parameters", {})
            description = str(config.get("description", ""))
            is_active = bool(config.get("is_active", True))
        else:
            # SQLAlchemy model or duck-typed object
            rule_id = str(getattr(config, "id", ""))
            name = str(getattr(config, "name", rule_id))
            dataset_id = str(getattr(config, "dataset_id", ""))
            category_raw = getattr(config, "category", "")
            severity_raw = getattr(config, "severity", RuleSeverity.HIGH)
            params = getattr(config, "parameters", {})
            description = str(getattr(config, "description", ""))
            is_active = bool(getattr(config, "is_active", True))

        # Deserialize parameters if JSON string (e.g. from SQLite DB column)
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except (json.JSONDecodeError, TypeError):
                params = {}

        if isinstance(category_raw, RuleCategory):
            category_key = category_raw.value
        else:
            category_key = str(category_raw).upper()

        rule_cls = cls.get_rule_class(category_key)
        if rule_cls is None:
            raise LuxException(
                code="UNKNOWN_RULE_CATEGORY",
                message=(
                    f"Unknown rule category '{category_raw}'. "
                    f"Available categories: {', '.join(cls.list_registered_categories())}."
                ),
                details={"category": category_raw, "rule_id": rule_id},
            )

        return rule_cls(
            rule_id=rule_id,
            name=name,
            dataset_id=dataset_id,
            category=category_raw,
            severity=severity_raw,
            parameters=params,
            description=description,
            is_active=is_active,
        )


# Register Core Evaluators
RuleRegistry.register(RuleCategory.NULL_CHECK, NullCheckRule)
RuleRegistry.register(RuleCategory.UNIQUENESS, UniquenessRule)
RuleRegistry.register(RuleCategory.TYPE_VALIDITY, TypeValidityRule)
RuleRegistry.register(RuleCategory.RECORD_COUNT, RecordCountRule)
RuleRegistry.register(RuleCategory.VALUE_RANGE, ValueRangeRule)

# Register Relational, Temporal, Schema, and Freshness Evaluators
RuleRegistry.register(RuleCategory.REFERENTIAL_INTEGRITY, ReferentialIntegrityRule)
RuleRegistry.register(RuleCategory.TEMPORAL_ANOMALY, TemporalAnomalyRule)
RuleRegistry.register(RuleCategory.SCHEMA_INTEGRITY, SchemaIntegrityRule)
RuleRegistry.register(RuleCategory.FRESHNESS, FreshnessRule)
