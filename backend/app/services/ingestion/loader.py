"""Scenario loader service parsing scenario definitions and populating SQLite persistence."""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import LuxException, NotFoundError
from app.models.dataset import Dataset
from app.models.investigation import Investigation, ReportArtifact
from app.models.lineage import LineageEdge, LineageNode
from app.models.pipeline import FreshnessCheck, PipelineRun
from app.models.scenario import Scenario
from app.models.validation import ValidationFinding, ValidationRule, ValidationRun
from app.schemas.dataset import DatasetResponse
from app.schemas.scenario import (
    LoadScenarioResponse,
    ScenarioDetail,
    ScenarioSummary,
)
from app.services.ingestion.reader import DatasetReader


def _parse_iso_datetime(value: str | None) -> datetime | None:
    """Safely parse ISO datetime string with optional Z suffix."""
    if not value:
        return None
    try:
        clean = value.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except (ValueError, TypeError):
        return None


class ScenarioLoaderService:
    """Service for discovering, inspecting, and loading bundled scenarios into SQLite."""

    @staticmethod
    def list_scenarios(db: Session) -> list[ScenarioSummary]:
        """List all available scenarios from the filesystem and database."""
        summaries: list[ScenarioSummary] = []
        scenarios_dir = settings.scenarios_dir

        if not scenarios_dir.exists():
            return summaries

        # Query database scenarios for active fixture versions
        db_scenarios = {s.id: s for s in db.execute(select(Scenario)).scalars().all()}

        for item in sorted(scenarios_dir.iterdir()):
            if item.is_dir():
                scenario_json_path = item / "scenario.json"
                if scenario_json_path.exists():
                    try:
                        with open(scenario_json_path, encoding="utf-8") as f:
                            meta = json.load(f)

                        scenario_id = meta.get("id", item.name)
                        db_record = db_scenarios.get(scenario_id)

                        # Determine active fixture version from DB or default to defective
                        active_version = (
                            db_record.active_fixture_version if db_record else "defective"
                        )

                        dataset_count = len(meta.get("datasets", []))
                        rule_count = 0

                        rules_json_path = item / "rules.json"
                        if rules_json_path.exists():
                            with open(rules_json_path, encoding="utf-8") as rf:
                                rules_meta = json.load(rf)
                                rule_count = len(rules_meta.get("rules", []))

                        summaries.append(
                            ScenarioSummary(
                                id=scenario_id,
                                name=meta.get("name", item.name),
                                description=meta.get("description"),
                                category=meta.get("category", "synthetic"),
                                is_bundled=True,
                                active_fixture_version=active_version,
                                dataset_count=dataset_count,
                                rule_count=rule_count,
                            )
                        )
                    except Exception:
                        continue

        return summaries

    @staticmethod
    def get_scenario_detail(scenario_id: str, db: Session) -> ScenarioDetail:
        """Retrieve detailed scenario metadata including registered datasets."""
        scenario_dir = settings.scenarios_dir / scenario_id
        scenario_json_path = scenario_dir / "scenario.json"

        if not scenario_json_path.exists():
            raise NotFoundError(
                code="SCENARIO_NOT_FOUND",
                message=f"Scenario with ID '{scenario_id}' was not found.",
            )

        with open(scenario_json_path, encoding="utf-8") as f:
            meta = json.load(f)

        db_scenario = db.execute(
            select(Scenario).where(Scenario.id == scenario_id)
        ).scalar_one_or_none()
        active_version = db_scenario.active_fixture_version if db_scenario else "defective"

        # Query loaded datasets from DB if scenario has been loaded
        db_datasets = (
            db.execute(select(Dataset).where(Dataset.scenario_id == scenario_id)).scalars().all()
            if db_scenario
            else []
        )

        dataset_responses: list[DatasetResponse] = []
        if db_datasets:
            dataset_responses = [
                DatasetResponse(
                    id=d.id,
                    scenario_id=d.scenario_id,
                    name=d.name,
                    format=d.file_format,
                    file_size_bytes=d.file_size_bytes,
                    record_count=d.record_count,
                    column_count=d.column_count,
                    created_at=d.created_at,
                )
                for d in db_datasets
            ]
        else:
            # Fallback to dataset metadata declared in scenario.json
            for d in meta.get("datasets", []):
                dataset_responses.append(
                    DatasetResponse(
                        id=d.get("id"),
                        scenario_id=scenario_id,
                        name=d.get("name", f"{d.get('id')}.csv"),
                        format=d.get("format", "csv"),
                        file_size_bytes=0,
                        record_count=d.get("expected_record_count", 0),
                        column_count=len(d.get("columns", [])),
                        created_at=None,
                    )
                )

        rule_count = 0
        rules_path = scenario_dir / "rules.json"
        if rules_path.exists():
            with open(rules_path, encoding="utf-8") as rf:
                rule_count = len(json.load(rf).get("rules", []))

        return ScenarioDetail(
            id=scenario_id,
            name=meta.get("name", scenario_id),
            description=meta.get("description"),
            category=meta.get("category", "synthetic"),
            is_bundled=True,
            active_fixture_version=active_version,
            dataset_count=len(dataset_responses),
            rule_count=rule_count,
            datasets=dataset_responses,
            created_at=db_scenario.created_at if db_scenario else None,
            updated_at=db_scenario.updated_at if db_scenario else None,
        )

    @staticmethod
    def load_scenario(
        scenario_id: str,
        fixture_version: str,
        db: Session,
    ) -> LoadScenarioResponse:
        """Load scenario datasets, rules, lineage DAG, and pipeline history into SQLite."""
        if fixture_version not in ("defective", "corrected"):
            raise LuxException(
                code="INVALID_FIXTURE_VERSION",
                message=(
                    f"Invalid fixture version '{fixture_version}'. "
                    "Must be 'defective' or 'corrected'."
                ),
            )

        scenario_dir = settings.scenarios_dir / scenario_id
        scenario_json_path = scenario_dir / "scenario.json"

        if not scenario_json_path.exists():
            raise NotFoundError(
                code="SCENARIO_NOT_FOUND",
                message=f"Scenario with ID '{scenario_id}' was not found at {scenario_json_path}.",
            )

        with open(scenario_json_path, encoding="utf-8") as f:
            scenario_meta = json.load(f)

        rules_meta: dict[str, Any] = {}
        rules_json_path = scenario_dir / "rules.json"
        if rules_json_path.exists():
            with open(rules_json_path, encoding="utf-8") as f:
                rules_meta = json.load(f)

        # Determine pipeline history file (check corrected subdirectory for corrected fixture)
        pipeline_meta: dict[str, Any] = {}
        pipeline_history_path = scenario_dir / "pipeline_history.json"
        if fixture_version == "corrected":
            corrected_pipe_path = scenario_dir / "corrected" / "pipeline_history.json"
            if corrected_pipe_path.exists():
                pipeline_history_path = corrected_pipe_path

        if pipeline_history_path.exists():
            with open(pipeline_history_path, encoding="utf-8") as f:
                pipeline_meta = json.load(f)

        # Clean existing dependent records for idempotent re-loading
        val_run_ids = select(ValidationRun.id).where(ValidationRun.scenario_id == scenario_id)
        db.execute(delete(ValidationFinding).where(ValidationFinding.run_id.in_(val_run_ids)))
        db.execute(delete(ValidationRun).where(ValidationRun.scenario_id == scenario_id))
        db.execute(delete(ReportArtifact).where(ReportArtifact.scenario_id == scenario_id))
        db.execute(delete(Investigation).where(Investigation.scenario_id == scenario_id))
        db.execute(delete(FreshnessCheck).where(FreshnessCheck.scenario_id == scenario_id))
        db.execute(delete(PipelineRun).where(PipelineRun.scenario_id == scenario_id))
        db.execute(delete(LineageEdge).where(LineageEdge.scenario_id == scenario_id))
        db.execute(delete(LineageNode).where(LineageNode.scenario_id == scenario_id))
        db.execute(delete(ValidationRule).where(ValidationRule.scenario_id == scenario_id))
        db.execute(delete(Dataset).where(Dataset.scenario_id == scenario_id))

        # Upsert Scenario
        db_scenario = db.execute(
            select(Scenario).where(Scenario.id == scenario_id)
        ).scalar_one_or_none()
        now = datetime.now(UTC)
        if db_scenario:
            db_scenario.name = scenario_meta.get("name", scenario_id)
            db_scenario.description = scenario_meta.get("description")
            db_scenario.category = scenario_meta.get("category", "synthetic")
            db_scenario.active_fixture_version = fixture_version
            db_scenario.updated_at = now
        else:
            db_scenario = Scenario(
                id=scenario_id,
                name=scenario_meta.get("name", scenario_id),
                description=scenario_meta.get("description"),
                category=scenario_meta.get("category", "synthetic"),
                is_bundled=True,
                active_fixture_version=fixture_version,
                created_at=now,
                updated_at=now,
            )
            db.add(db_scenario)

        db.flush()

        # Ingest Datasets
        loaded_datasets: list[str] = []
        for dataset_def in scenario_meta.get("datasets", []):
            d_id = dataset_def["id"]
            d_name = dataset_def.get("name", f"{d_id}.csv")
            d_format = dataset_def.get("format", "csv").lower()

            # Resolve fixture file path for selected version
            fixture_subpath = (
                dataset_def.get(f"{fixture_version}_path") or f"{fixture_version}/{d_name}"
            )
            file_path = (scenario_dir / fixture_subpath).resolve()

            if not file_path.exists():
                raise NotFoundError(
                    code="FIXTURE_FILE_NOT_FOUND",
                    message=f"Fixture file '{fixture_subpath}' not found for dataset '{d_id}'.",
                )

            # Inspect and extract dataset metadata
            record_count, columns, schemas = DatasetReader.inspect_file(file_path, d_format)
            file_size_bytes = file_path.stat().st_size

            # If scenario.json declared columns, merge or prioritize them
            schema_json = json.dumps([s.model_dump() for s in schemas])

            dataset = Dataset(
                id=d_id,
                scenario_id=scenario_id,
                name=d_name,
                file_path=str(file_path),
                file_format=d_format,
                file_size_bytes=file_size_bytes,
                record_count=record_count,
                column_count=len(columns),
                schema_definition=schema_json,
                created_at=now,
            )
            db.add(dataset)
            loaded_datasets.append(d_id)

        db.flush()

        # Ingest Validation Rules
        rules_registered = 0
        for rule_def in rules_meta.get("rules", []):
            rule_id = rule_def["id"]
            dataset_id = rule_def["dataset_id"]
            # Ensure dataset exists before adding rule
            if dataset_id in loaded_datasets:
                rule = ValidationRule(
                    id=rule_id,
                    scenario_id=scenario_id,
                    dataset_id=dataset_id,
                    name=rule_def["name"],
                    category=rule_def["category"],
                    severity=rule_def["severity"],
                    parameters=json.dumps(rule_def.get("parameters", {})),
                    is_active=rule_def.get("is_active", True),
                    created_at=now,
                )
                db.add(rule)
                rules_registered += 1

        # Ingest Lineage Nodes & Edges
        lineage_meta = scenario_meta.get("lineage", {})
        lineage_nodes_loaded = 0
        for node_def in lineage_meta.get("nodes", []):
            node_id = node_def["id"]
            dataset_fk = node_def.get("dataset_id")
            if dataset_fk and dataset_fk not in loaded_datasets:
                dataset_fk = None

            node_metadata = (
                json.dumps(node_def["metadata"])
                if "metadata" in node_def and node_def["metadata"]
                else None
            )

            node = LineageNode(
                id=node_id,
                scenario_id=scenario_id,
                name=node_def["name"],
                node_type=node_def["type"],
                dataset_id=dataset_fk,
                owner=node_def.get("owner"),
                description=node_def.get("description"),
                node_metadata=node_metadata,
            )
            db.add(node)
            lineage_nodes_loaded += 1

        db.flush()

        for edge_def in lineage_meta.get("edges", []):
            edge_id = f"{edge_def['source']}->{edge_def['target']}"
            edge = LineageEdge(
                id=edge_id,
                scenario_id=scenario_id,
                source_id=edge_def["source"],
                target_id=edge_def["target"],
                dependency_type=edge_def.get("dependency_type", "DIRECT_INPUT"),
            )
            db.add(edge)

        # Ingest Pipeline Runs & Freshness Checks
        for run_def in pipeline_meta.get("pipeline_runs", []):
            run_id = run_def["id"]
            start_dt = _parse_iso_datetime(run_def.get("start_time")) or now
            end_dt = _parse_iso_datetime(run_def.get("end_time")) or now
            run_log_str = (
                json.dumps(run_def["run_log"])
                if "run_log" in run_def and run_def["run_log"]
                else None
            )

            pipe_run = PipelineRun(
                id=run_id,
                scenario_id=scenario_id,
                pipeline_name=run_def.get("pipeline_name", "default_pipeline"),
                execution_status=run_def.get("execution_status", "COMPLETED_SUCCESS"),
                quality_health=run_def.get("quality_health", "HEALTHY"),
                start_time=start_dt,
                end_time=end_dt,
                duration_ms=run_def.get("duration_ms", 0),
                records_ingested=run_def.get("records_ingested", 0),
                records_written=run_def.get("records_written", 0),
                error_message=run_def.get("error_message"),
                run_log=run_log_str,
                created_at=now,
            )
            db.add(pipe_run)

        for check_def in pipeline_meta.get("freshness_checks", []):
            check_id = check_def["id"]
            dataset_id = check_def["dataset_id"]
            if dataset_id not in loaded_datasets:
                continue

            exp_dt = _parse_iso_datetime(check_def.get("expected_partition_timestamp")) or now
            obs_dt = _parse_iso_datetime(check_def.get("observed_partition_timestamp")) or now
            chk_dt = _parse_iso_datetime(check_def.get("checked_at")) or now

            fresh_check = FreshnessCheck(
                id=check_id,
                scenario_id=scenario_id,
                dataset_id=dataset_id,
                expected_partition_timestamp=exp_dt,
                observed_partition_timestamp=obs_dt,
                sla_hours=check_def.get("sla_hours", 24),
                status=check_def.get("status", "FRESH"),
                checked_at=chk_dt,
            )
            db.add(fresh_check)

        db.commit()

        scenario_title = scenario_meta.get("name", scenario_id)
        return LoadScenarioResponse(
            scenario_id=scenario_id,
            active_fixture_version=fixture_version,
            loaded_datasets=loaded_datasets,
            rules_registered=rules_registered,
            lineage_nodes_loaded=lineage_nodes_loaded,
            message=(
                f"Scenario '{scenario_title}' loaded successfully with {fixture_version} fixtures."
            ),
        )
