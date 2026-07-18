"""Upload size limits and magic-byte content validation for /predict."""

from __future__ import annotations

from typing import Literal

from fastapi import HTTPException, UploadFile

from backend.config import MAX_IMAGE_SIZE_BYTES, MAX_IMAGE_SIZE_MB, MAX_VIDEO_SIZE_BYTES, MAX_VIDEO_SIZE_MB

MediaKind = Literal["image", "video"]

_CHUNK_SIZE = 1024 * 1024
_UNSUPPORTED_DETAIL = (
    "Unsupported file type. Please upload a JPG, PNG, GIF, or WebP image, "
    "or an MP4, AVI, or MOV video."
)


def detect_media_kind(header: bytes) -> MediaKind | None:
    """Identify image vs video from file magic bytes (first ~12 bytes)."""
    if len(header) < 4:
        return None

    if header[:3] == b"\xff\xd8\xff":
        return "image"

    if len(header) >= 8 and header[:8] == b"\x89PNG\r\n\x1a\n":
        return "image"

    if header[:6] in (b"GIF87a", b"GIF89a"):
        return "image"

    if header[:4] == b"RIFF" and len(header) >= 12:
        if header[8:12] == b"WEBP":
            return "image"
        if header[8:12] == b"AVI ":
            return "video"

    if len(header) >= 8 and header[4:8] == b"ftyp":
        return "video"

    return None


def _payload_too_large_detail(kind: MediaKind, size_bytes: int) -> str:
    size_mb = size_bytes / (1024 * 1024)
    max_mb = MAX_IMAGE_SIZE_MB if kind == "image" else MAX_VIDEO_SIZE_MB
    media_label = "image" if kind == "image" else "video"
    return (
        f"This {media_label} is too large ({size_mb:.1f} MB). "
        f"The maximum allowed size is {max_mb} MB."
    )


async def read_and_validate_upload(upload: UploadFile) -> tuple[bytes, MediaKind]:
    """
    Read an upload with a type-specific size cap and validate content via magic bytes.
    Raises HTTPException(413) when over limit, HTTPException(415) for invalid content.
    """
    header = await upload.read(12)
    if not header:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    media_kind = detect_media_kind(header)
    if media_kind is None:
        raise HTTPException(status_code=415, detail=_UNSUPPORTED_DETAIL)

    max_bytes = MAX_IMAGE_SIZE_BYTES if media_kind == "image" else MAX_VIDEO_SIZE_BYTES
    chunks = [header]
    total = len(header)

    while True:
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=_payload_too_large_detail(media_kind, total),
            )

        chunk = await upload.read(_CHUNK_SIZE)
        if not chunk:
            break

        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=_payload_too_large_detail(media_kind, total),
            )
        chunks.append(chunk)

    return b"".join(chunks), media_kind
