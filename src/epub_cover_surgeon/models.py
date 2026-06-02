"""Typed result objects for epub-cover-surgeon."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ValidationResult:
    """Result from an EPUB validation pass."""

    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CoverInfo:
    """Location and metadata for an EPUB cover image."""

    item_id: str | None
    href: str | None
    path: str | None
    media_type: str | None
    size_bytes: int | None = None


@dataclass(frozen=True)
class EpubInfo:
    """Human- and machine-readable EPUB inspection summary."""

    path: Path
    title: str | None
    authors: list[str]
    language: str | None
    package_path: str | None
    version: str | None
    has_cover: bool
    cover: CoverInfo | None
    is_drm_protected: bool
    manifest_count: int
    spine_count: int
    validation: ValidationResult


@dataclass(frozen=True)
class ExtractedCover:
    """Extracted cover payload returned by the Python API."""

    data: bytes
    media_type: str
    filename: str
    source_path: str


@dataclass(frozen=True)
class ReplacementResult:
    """Result from a cover replacement or hardening operation."""

    output_path: Path
    validation: ValidationResult
    cover: CoverInfo | None
