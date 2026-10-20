"""Datasets API endpoints for discovery, previewing, and secure uploading."""

import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.session import get_db
from app.models.dataset import Dataset
from app.models.scenario import Scenario
from app.schemas.dataset import (
    DatasetPreviewResponse,
    DatasetResponse,
    DatasetUploadResponse,
)
from app.services.ingestion.reader import DatasetReader
from app.services.ingestion.security import save_upload_file_securely

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get(
    "",
    response_model=list[DatasetResponse],
    status_code=status.HTTP_200_OK,
    summary="List Datasets",
    description="Retrieve all ingested datasets, optionally filtered by scenario.",
)
def list_datasets(
    scenario_id: str | None = Query(None, description="Filter by parent scenario ID"),
    db: Session = Depends(get_db),
) -> list[DatasetResponse]:
    """List datasets with optional scenario filter."""
    stmt = select(Dataset)
    if scenario_id:
        stmt = stmt.where(Dataset.scenario_id == scenario_id)

    datasets = db.execute(stmt).scalars().all()
    return [
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
        for d in datasets
    ]


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Dataset Metadata",
    description="Retrieve metadata for a specific dataset by ID.",
)
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
) -> DatasetResponse:
    """Get dataset metadata by ID."""
    dataset = db.execute(select(Dataset).where(Dataset.id == dataset_id)).scalar_one_or_none()
    if not dataset:
        raise NotFoundError(
            code="DATASET_NOT_FOUND",
            message=f"Dataset with ID '{dataset_id}' was not found.",
            details={"dataset_id": dataset_id},
        )

    return DatasetResponse(
        id=dataset.id,
        scenario_id=dataset.scenario_id,
        name=dataset.name,
        format=dataset.file_format,
        file_size_bytes=dataset.file_size_bytes,
        record_count=dataset.record_count,
        column_count=dataset.column_count,
        created_at=dataset.created_at,
    )


@router.get(
    "/{dataset_id}/preview",
    response_model=DatasetPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview Dataset Rows",
    description="Retrieve a paginated preview of dataset rows (max 100 rows per request).",
)
def preview_dataset(
    dataset_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of rows to return (1-100)"),
    offset: int = Query(0, ge=0, description="Row offset for pagination"),
    db: Session = Depends(get_db),
) -> DatasetPreviewResponse:
    """Retrieve paginated rows for a dataset."""
    dataset = db.execute(select(Dataset).where(Dataset.id == dataset_id)).scalar_one_or_none()
    if not dataset:
        raise NotFoundError(
            code="DATASET_NOT_FOUND",
            message=f"Dataset with ID '{dataset_id}' does not exist.",
            details={"dataset_id": dataset_id},
        )

    file_path = Path(dataset.file_path)
    total_records, columns, rows = DatasetReader.read_preview(
        file_path=file_path,
        file_format=dataset.file_format,
        limit=limit,
        offset=offset,
    )

    return DatasetPreviewResponse(
        dataset_id=dataset.id,
        total_records=total_records,
        limit=limit,
        offset=offset,
        columns=columns,
        rows=rows,
    )


@router.post(
    "/upload",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Custom Dataset",
    description="Securely upload a CSV or JSON dataset (max 20MB) to an isolated workspace.",
)
async def upload_dataset(
    file: UploadFile = File(..., description="CSV or JSON dataset file (max 20MB)"),
    scenario_id: str | None = Form(None, description="Target scenario identifier"),
    dataset_name: str | None = Form(None, description="Custom display name for the dataset"),
    db: Session = Depends(get_db),
) -> DatasetUploadResponse:
    """Handle secure dataset file upload."""
    (
        target_file,
        sanitized_filename,
        file_format,
        total_bytes,
    ) = await save_upload_file_securely(file)

    # Inspect the saved file to extract record count and schema
    record_count, columns, schemas = DatasetReader.inspect_file(target_file, file_format)

    # Resolve or create scenario record
    target_scenario_id = scenario_id or "custom_uploads"
    sc = db.execute(select(Scenario).where(Scenario.id == target_scenario_id)).scalar_one_or_none()
    now = datetime.now(UTC)
    if not sc:
        sc = Scenario(
            id=target_scenario_id,
            name=target_scenario_id.replace("_", " ").title(),
            description="Scenario containing custom uploaded datasets.",
            category="custom",
            is_bundled=False,
            active_fixture_version="custom",
            created_at=now,
            updated_at=now,
        )
        db.add(sc)
        db.flush()

    upload_id = target_file.parent.name
    dataset_id = f"upload_{upload_id}"
    display_name = dataset_name or sanitized_filename

    schema_json = json.dumps([s.model_dump() for s in schemas])
    dataset = Dataset(
        id=dataset_id,
        scenario_id=sc.id,
        name=display_name,
        file_path=str(target_file),
        file_format=file_format,
        file_size_bytes=total_bytes,
        record_count=record_count,
        column_count=len(columns),
        schema_definition=schema_json,
        created_at=now,
    )
    db.add(dataset)
    db.commit()

    return DatasetUploadResponse(
        dataset_id=dataset_id,
        name=display_name,
        format=file_format,
        file_size_bytes=total_bytes,
        record_count=record_count,
        column_count=len(columns),
    )
