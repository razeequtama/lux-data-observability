"""Unit tests for Ingestion Service, Reader, and Security Handlers."""

import io
from pathlib import Path

import pytest

from app.core.errors import LuxException, NotFoundError
from app.services.ingestion.reader import DatasetReader, _cast_value, _infer_type
from app.services.ingestion.security import (
    sniff_content_safety,
    validate_filename,
)


def test_infer_type() -> None:
    """Test data type inference logic."""
    assert _infer_type("123") == "integer"
    assert _infer_type("-456") == "integer"
    assert _infer_type("3.1415") == "float"
    assert _infer_type("true") == "boolean"
    assert _infer_type("FALSE") == "boolean"
    assert _infer_type("2026-10-19T08:14:22Z") == "timestamp"
    assert _infer_type("2026-10-19 08:14:22") == "timestamp"
    assert _infer_type("hello world") == "string"
    assert _infer_type("   ") == "string"


def test_cast_value() -> None:
    """Test value casting logic."""
    assert _cast_value("100") == 100
    assert _cast_value("100.5") == 100.5
    assert _cast_value("true") is True
    assert _cast_value("false") is False
    assert _cast_value("") is None
    assert _cast_value("  ") is None
    assert _cast_value("ORD-1001") == "ORD-1001"


def test_validate_filename_safe() -> None:
    """Test filename validation on valid CSV and JSON filenames."""
    assert validate_filename("dataset.csv") == "dataset.csv"
    assert validate_filename("MY_FILE.JSON") == "MY_FILE.JSON"
    assert validate_filename("orders-2026_10.csv") == "orders-2026_10.csv"


def test_validate_filename_path_traversal() -> None:
    """Test path traversal patterns rejection."""
    with pytest.raises(LuxException) as exc1:
        validate_filename("../../etc/passwd")
    assert exc1.value.code == "PATH_TRAVERSAL_DETECTED"

    with pytest.raises(LuxException) as exc2:
        validate_filename("..\\windows\\system32.csv")
    assert exc2.value.code == "PATH_TRAVERSAL_DETECTED"

    with pytest.raises(LuxException) as exc3:
        validate_filename("orders.csv\x00.exe")
    assert exc3.value.code == "PATH_TRAVERSAL_DETECTED"


def test_validate_filename_disallowed_extension() -> None:
    """Test non-whitelisted extensions rejection."""
    with pytest.raises(LuxException) as exc1:
        validate_filename("malware.exe")
    assert exc1.value.code == "UNSUPPORTED_FILE_TYPE"

    with pytest.raises(LuxException) as exc2:
        validate_filename("script.py")
    assert exc2.value.code == "UNSUPPORTED_FILE_TYPE"


def test_sniff_content_safety_binary_and_archives() -> None:
    """Test content sniffing flags binary executables and compressed archives."""
    # Binary with null byte
    with pytest.raises(LuxException) as exc1:
        sniff_content_safety(io.BytesIO(b"\x7fELF\x02\x01\x01\x00\x00"), "csv")
    assert exc1.value.code == "BINARY_FILE_REJECTED"

    # Zip archive header
    with pytest.raises(LuxException) as exc2:
        sniff_content_safety(io.BytesIO(b"PK\x03\x04\x14\x00\x00\x00"), "csv")
    assert exc2.value.code == "ARCHIVE_FILE_REJECTED"

    # Empty stream
    with pytest.raises(LuxException) as exc3:
        sniff_content_safety(io.BytesIO(b""), "csv")
    assert exc3.value.code == "EMPTY_FILE"


def test_dataset_reader_file_not_found(tmp_path: Path) -> None:
    """Test DatasetReader raises NotFoundError on non-existent file."""
    missing = tmp_path / "does_not_exist.csv"
    with pytest.raises(NotFoundError):
        DatasetReader.inspect_file(missing, "csv")
