"""Basic EPUB validation."""

from __future__ import annotations

import zipfile
from pathlib import Path

from .metadata import (
    find_cover_item,
    manifest_items,
    open_epub,
    read_package_document,
    spine_itemrefs,
)
from .models import ValidationResult


def is_drm_protected(path: str | Path) -> bool:
    """Return True if common EPUB DRM indicator files are present."""

    with open_epub(path) as epub_zip:
        names = set(epub_zip.namelist())
        return "META-INF/encryption.xml" in names or "META-INF/rights.xml" in names


def validate_epub(path: str | Path, *, require_cover: bool = False) -> ValidationResult:
    """Validate the basic structure needed for safe cover operations."""

    errors: list[str] = []
    warnings: list[str] = []
    epub_path = Path(path)

    try:
        if not epub_path.is_file():
            return ValidationResult(False, [f"File not found: {epub_path}"], [])
        if epub_path.suffix.lower() != ".epub":
            errors.append("File extension is not .epub")
        if epub_path.stat().st_size == 0:
            errors.append("File is empty")
        if not zipfile.is_zipfile(epub_path):
            return ValidationResult(False, errors + ["File is not a ZIP archive"], warnings)

        with open_epub(epub_path) as epub_zip:
            names = set(epub_zip.namelist())
            if "mimetype" not in names:
                warnings.append("Missing mimetype entry")
            else:
                mimetype = epub_zip.read("mimetype").decode("ascii", "replace").strip()
                if mimetype != "application/epub+zip":
                    errors.append("mimetype entry is not application/epub+zip")

            package = read_package_document(epub_zip)
            items = manifest_items(package.root)
            itemrefs = spine_itemrefs(package.root)
            if not items:
                errors.append("Package manifest is empty")
            if not itemrefs:
                warnings.append("Package spine is empty")

            cover_item, _cover_id, cover_path = find_cover_item(package)
            if require_cover and cover_item is None:
                errors.append("No EPUB cover is declared")
            if cover_item is not None:
                media_type = cover_item.get("media-type") or ""
                if not media_type.startswith("image/"):
                    errors.append("Declared cover manifest item is not an image")
                if not cover_path:
                    errors.append("Declared cover manifest item is missing href")
                elif cover_path not in names:
                    errors.append(f"Declared cover image is missing from archive: {cover_path}")

            if "META-INF/encryption.xml" in names or "META-INF/rights.xml" in names:
                warnings.append("Common DRM indicator file is present")

    except Exception as exc:  # noqa: BLE001 - public validator should return readable errors.
        errors.append(str(exc))

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)
