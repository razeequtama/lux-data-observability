"""Chunked dataset reader, metadata extractor, and paginated preview provider."""

import csv
import json
from pathlib import Path
from typing import Any

from app.core.errors import LuxException, NotFoundError
from app.schemas.dataset import ColumnSchema

# Maximum permitted preview page size per security spec
MAX_PREVIEW_LIMIT = 100


def _infer_type(value: str) -> str:
    """Infer basic data type from string representation."""
    cleaned = value.strip()
    if not cleaned:
        return "string"
    if cleaned.lower() in ("true", "false"):
        return "boolean"
    try:
        int(cleaned)
        return "integer"
    except ValueError:
        pass
    try:
        float(cleaned)
        return "float"
    except ValueError:
        pass
    # Basic timestamp heuristic (ISO format contains T or dashes and colons)
    if ("-" in cleaned and ":" in cleaned) or ("T" in cleaned and "Z" in cleaned):
        return "timestamp"
    return "string"


def _cast_value(value: str) -> Any:
    """Cast a CSV string cell to a typed Python object for JSON representation."""
    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.lower() == "true":
        return True
    if cleaned.lower() == "false":
        return False
    try:
        return int(cleaned)
    except ValueError:
        pass
    try:
        return float(cleaned)
    except ValueError:
        pass
    return value


class DatasetReader:
    """Reader service for CSV and JSON datasets."""

    @staticmethod
    def inspect_file(
        file_path: Path, file_format: str
    ) -> tuple[int, list[str], list[ColumnSchema]]:
        """Inspect file and extract record count, column names, and column schemas.

        Returns:
            Tuple of (record_count, column_names, column_schemas)
        """
        if not file_path.exists() or not file_path.is_file():
            raise NotFoundError(
                code="FILE_NOT_FOUND",
                message=f"Dataset file at '{file_path}' does not exist.",
            )

        format_lower = file_format.lower()
        if format_lower == "csv":
            return DatasetReader._inspect_csv(file_path)
        elif format_lower == "json":
            return DatasetReader._inspect_json(file_path)
        else:
            raise LuxException(
                code="UNSUPPORTED_FORMAT",
                message=f"Unsupported dataset format '{file_format}'. Must be 'csv' or 'json'.",
            )

    @staticmethod
    def _inspect_csv(file_path: Path) -> tuple[int, list[str], list[ColumnSchema]]:
        """Extract metadata from CSV using streaming line reader."""
        try:
            with open(file_path, encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.reader(f)
                try:
                    headers = next(reader)
                except StopIteration:
                    return 0, [], []

                columns = [h.strip() for h in headers if h.strip()]
                if not columns:
                    return 0, [], []

                # Track nullability and sample types
                column_types: dict[str, str] = {c: "string" for c in columns}
                column_nullable: dict[str, bool] = {c: False for c in columns}
                count = 0

                for row in reader:
                    count += 1
                    for idx, col in enumerate(columns):
                        val = row[idx] if idx < len(row) else ""
                        if not val.strip():
                            column_nullable[col] = True
                        elif count <= 100 and column_types[col] == "string":
                            inferred = _infer_type(val)
                            if inferred != "string":
                                column_types[col] = inferred

                schemas = [
                    ColumnSchema(
                        name=col,
                        type=column_types.get(col, "string"),
                        nullable=column_nullable.get(col, True),
                    )
                    for col in columns
                ]
                return count, columns, schemas
        except Exception as exc:
            raise LuxException(
                code="MALFORMED_CSV",
                message=f"Failed to parse CSV dataset: {exc}",
            ) from exc

    @staticmethod
    def _inspect_json(file_path: Path) -> tuple[int, list[str], list[ColumnSchema]]:
        """Extract metadata from JSON dataset."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            records: list[dict[str, Any]]
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                # If wrapped in a dictionary key like "records" or "items"
                if "records" in data and isinstance(data["records"], list):
                    records = data["records"]
                elif "data" in data and isinstance(data["data"], list):
                    records = data["data"]
                else:
                    records = [data]
            else:
                raise LuxException(
                    code="MALFORMED_JSON",
                    message="JSON dataset must be an array of objects or an object.",
                )

            if not records:
                return 0, [], []

            sample = records[0]
            columns = list(sample.keys()) if isinstance(sample, dict) else []

            schemas = []
            for col in columns:
                val = sample.get(col)
                inferred = "string"
                if isinstance(val, bool):
                    inferred = "boolean"
                elif isinstance(val, int):
                    inferred = "integer"
                elif isinstance(val, float):
                    inferred = "float"
                elif isinstance(val, dict | list):
                    inferred = "json"
                schemas.append(
                    ColumnSchema(
                        name=col,
                        type=inferred,
                        nullable=any(
                            r.get(col) is None for r in records[:100] if isinstance(r, dict)
                        ),
                    )
                )

            return len(records), columns, schemas
        except json.JSONDecodeError as exc:
            raise LuxException(
                code="MALFORMED_JSON",
                message=f"Invalid JSON in dataset file: {exc}",
            ) from exc

    @staticmethod
    def read_preview(
        file_path: Path,
        file_format: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[str], list[dict[str, Any]]]:
        """Read paginated rows from dataset file.

        Returns:
            Tuple of (total_records, column_names, paginated_rows)
        """
        if not file_path.exists() or not file_path.is_file():
            raise NotFoundError(
                code="FILE_NOT_FOUND",
                message=f"Dataset file at '{file_path}' does not exist.",
            )

        limit = max(1, min(limit, MAX_PREVIEW_LIMIT))
        offset = max(0, offset)

        format_lower = file_format.lower()
        if format_lower == "csv":
            return DatasetReader._read_csv_preview(file_path, limit, offset)
        elif format_lower == "json":
            return DatasetReader._read_json_preview(file_path, limit, offset)
        else:
            raise LuxException(
                code="UNSUPPORTED_FORMAT",
                message=f"Unsupported format '{file_format}'.",
            )

    @staticmethod
    def _read_csv_preview(
        file_path: Path,
        limit: int,
        offset: int,
    ) -> tuple[int, list[str], list[dict[str, Any]]]:
        """Stream CSV file and collect requested page of rows."""
        try:
            with open(file_path, encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.DictReader(f)
                columns = reader.fieldnames or []
                total_records = 0
                rows: list[dict[str, Any]] = []

                for row_idx, raw_row in enumerate(reader):
                    total_records += 1
                    if offset <= row_idx < offset + limit:
                        typed_row = {k: _cast_value(v) for k, v in raw_row.items()}
                        rows.append(typed_row)

                return total_records, list(columns), rows
        except Exception as exc:
            raise LuxException(
                code="MALFORMED_CSV",
                message=f"Failed to read CSV preview: {exc}",
            ) from exc

    @staticmethod
    def _read_json_preview(
        file_path: Path,
        limit: int,
        offset: int,
    ) -> tuple[int, list[str], list[dict[str, Any]]]:
        """Read requested page of rows from JSON file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            records: list[dict[str, Any]]
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                if "records" in data and isinstance(data["records"], list):
                    records = data["records"]
                elif "data" in data and isinstance(data["data"], list):
                    records = data["data"]
                else:
                    records = [data]
            else:
                return 0, [], []

            total_records = len(records)
            columns = list(records[0].keys()) if records and isinstance(records[0], dict) else []
            rows = records[offset : offset + limit]
            return total_records, columns, rows
        except json.JSONDecodeError as exc:
            raise LuxException(
                code="MALFORMED_JSON",
                message=f"Failed to read JSON preview: {exc}",
            ) from exc
