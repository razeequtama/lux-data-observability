"""Upload security validation, path traversal prevention, and isolated file storage."""

import re
import urllib.parse
import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import LuxException, PayloadTooLargeError

ALLOWED_EXTENSIONS = {".csv", ".json"}
CHUNK_SIZE_BYTES = 64 * 1024  # 64 KB read buffer


def validate_filename(filename: str | None) -> str:
    """Validate filename against path traversal attacks and extension whitelists.

    Raises:
        LuxException: If path traversal or disallowed extension is detected.
    """
    if not filename or not filename.strip():
        raise LuxException(
            code="INVALID_FILENAME",
            message="Uploaded file must have a non-empty filename.",
        )

    decoded = urllib.parse.unquote(filename)

    # Check for null bytes (raw or URL-encoded)
    if "\x00" in filename or "\x00" in decoded or "%00" in filename.lower():
        raise LuxException(
            code="PATH_TRAVERSAL_DETECTED",
            message="Path traversal attempt detected: null byte in filename.",
        )

    # Check for path traversal characters in raw or decoded filename
    if ".." in filename or "/" in filename or "\\" in filename:
        raise LuxException(
            code="PATH_TRAVERSAL_DETECTED",
            message="Path traversal attempt detected in filename.",
        )
    if ".." in decoded or "/" in decoded or "\\" in decoded:
        raise LuxException(
            code="PATH_TRAVERSAL_DETECTED",
            message="Path traversal attempt detected in filename.",
        )

    # Path traversal regex check
    if re.search(r"(\.\./|\.\.\\)", filename) or re.search(r"(\.\./|\.\.\\)", decoded):
        raise LuxException(
            code="PATH_TRAVERSAL_DETECTED",
            message="Path traversal attempt detected in filename.",
        )

    clean_name = Path(filename).name
    ext = Path(clean_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise LuxException(
            code="UNSUPPORTED_FILE_TYPE",
            message=f"Disallowed file extension '{ext}'. Only .csv and .json files are permitted.",
        )

    return clean_name


def sniff_content_safety(stream: BinaryIO, ext: str) -> None:
    """Sniff initial bytes of stream for binary executables, zip bombs, or corrupt data."""
    pos = stream.tell()
    sample = stream.read(4096)
    stream.seek(pos)

    if not sample:
        raise LuxException(
            code="EMPTY_FILE",
            message="Uploaded file is empty.",
        )

    # Check for zip archive signature (PK\x03\x04)
    if sample.startswith(b"PK\x03\x04"):
        raise LuxException(
            code="ARCHIVE_FILE_REJECTED",
            message="Compressed archives are not supported for dataset uploads.",
        )

    # Check for null bytes (indicative of binary/executable formats)
    if b"\x00" in sample:
        raise LuxException(
            code="BINARY_FILE_REJECTED",
            message="Binary content or null-byte sequence detected in upload.",
        )

    # Verify UTF-8 decodeability on initial chunk
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LuxException(
            code="INVALID_ENCODING",
            message="Uploaded dataset must be UTF-8 encoded text.",
        ) from exc


async def save_upload_file_securely(
    upload_file: UploadFile,
    max_size_bytes: int | None = None,
) -> tuple[Path, str, str, int]:
    """Securely stream and save uploaded file to an isolated UUID directory.

    Returns:
        Tuple of (saved_file_path, sanitized_filename, file_format, total_bytes)

    Raises:
        LuxException: On validation failure or path traversal attempt.
        PayloadTooLargeError: If file exceeds maximum allowed bytes (20MB).
    """
    if max_size_bytes is None:
        max_size_bytes = settings.max_upload_size_bytes

    original_filename = upload_file.filename or "upload.csv"
    sanitized_filename = validate_filename(original_filename)
    file_format = Path(sanitized_filename).suffix.lstrip(".").lower()

    # Pre-check content safety if file object has read/seek
    if upload_file.file:
        sniff_content_safety(upload_file.file, file_format)

    # Generate isolated directory
    upload_id = str(uuid.uuid4())
    isolated_dir = (settings.uploads_dir / upload_id).resolve()
    isolated_dir.mkdir(parents=True, exist_ok=True)

    target_file = (isolated_dir / sanitized_filename).resolve()

    # Canonical path traversal boundary check
    if not target_file.is_relative_to(settings.uploads_dir.resolve()):
        raise LuxException(
            code="PATH_TRAVERSAL_DETECTED",
            message="Resolved path traverses outside of the designated uploads directory.",
        )

    # Stream to disk with size accounting
    total_bytes = 0
    try:
        with open(target_file, "wb") as out_file:
            while chunk := await upload_file.read(CHUNK_SIZE_BYTES):
                total_bytes += len(chunk)
                if total_bytes > max_size_bytes:
                    out_file.close()
                    # Clean up partial file on disk
                    if target_file.exists():
                        target_file.unlink()
                    if isolated_dir.exists():
                        isolated_dir.rmdir()
                    max_mb = max_size_bytes // (1024 * 1024)
                    raise PayloadTooLargeError(
                        code="PAYLOAD_TOO_LARGE",
                        message=f"Uploaded file exceeds maximum allowed limit ({max_mb}MB).",
                        details={
                            "file_size_bytes": total_bytes,
                            "max_allowed_bytes": max_size_bytes,
                        },
                    )
                out_file.write(chunk)
    except Exception:
        # Clean up partial file on failure
        if target_file.exists():
            target_file.unlink()
        if isolated_dir.exists() and not any(isolated_dir.iterdir()):
            isolated_dir.rmdir()
        raise

    return target_file, sanitized_filename, file_format, total_bytes
