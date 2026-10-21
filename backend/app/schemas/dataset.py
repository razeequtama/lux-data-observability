"""Pydantic schemas for datasets and file previews."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ColumnSchema(BaseModel):
    """Dataset column metadata schema."""

    name: str = Field(..., description="Column header name")
    type: str = Field(default="string", description="Inferred or declared data type")
    nullable: bool = Field(default=True, description="Whether null/empty values are permitted")


class DatasetResponse(BaseModel):
    """Dataset summary schema conforming to API contract."""

    id: str = Field(..., description="Dataset unique identifier")
    scenario_id: str = Field(..., description="Parent scenario identifier")
    name: str = Field(..., description="Filename or display name")
    format: str = Field(..., description="File format: csv or json")
    file_size_bytes: int = Field(..., description="File size in bytes")
    record_count: int = Field(..., description="Total row or record count")
    column_count: int = Field(..., description="Total column count")
    created_at: datetime | str | None = Field(default=None, description="Ingestion timestamp")


class DatasetPreviewResponse(BaseModel):
    """Paginated dataset row preview schema."""

    dataset_id: str = Field(..., description="Dataset identifier")
    total_records: int = Field(..., description="Total records in the dataset")
    limit: int = Field(..., description="Page size limit applied")
    offset: int = Field(..., description="Record offset applied")
    columns: list[str] = Field(..., description="Ordered list of column names")
    rows: list[dict[str, Any]] = Field(..., description="List of row objects")


class DatasetUploadResponse(BaseModel):
    """Response returned upon successful dataset upload."""

    dataset_id: str = Field(..., description="Generated dataset identifier")
    name: str = Field(..., description="Sanitized dataset filename")
    format: str = Field(..., description="File format: csv or json")
    file_size_bytes: int = Field(..., description="Stored file size in bytes")
    record_count: int = Field(..., description="Extracted record count")
    column_count: int = Field(..., description="Extracted column count")
