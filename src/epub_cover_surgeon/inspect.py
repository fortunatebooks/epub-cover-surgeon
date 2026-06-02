"""EPUB inspection API."""

from __future__ import annotations

from pathlib import Path

from .metadata import (
    find_cover_item,
    manifest_items,
    open_epub,
    read_package_document,
    spine_itemrefs,
    text_values,
)
from .models import CoverInfo, EpubInfo
from .validate import is_drm_protected, validate_epub


def inspect_epub(path: str | Path) -> EpubInfo:
    """Inspect title, authors, package basics, cover status, and validation."""

    epub_path = Path(path)
    validation = validate_epub(epub_path)

    title: str | None = None
    authors: list[str] = []
    language: str | None = None
    package_path: str | None = None
    version: str | None = None
    manifest_count = 0
    spine_count = 0
    cover: CoverInfo | None = None

    with open_epub(epub_path) as epub_zip:
        package = read_package_document(epub_zip)
        package_path = package.path
        version = package.root.get("version")
        titles = text_values(package.root, "title")
        title = titles[0] if titles else None
        authors = text_values(package.root, "creator")
        languages = text_values(package.root, "language")
        language = languages[0] if languages else None
        manifest_count = len(manifest_items(package.root))
        spine_count = len(spine_itemrefs(package.root))

        cover_item, cover_id, cover_path = find_cover_item(package)
        if cover_item is not None:
            size = None
            if cover_path and cover_path in epub_zip.namelist():
                size = epub_zip.getinfo(cover_path).file_size
            cover = CoverInfo(
                item_id=cover_id or cover_item.get("id"),
                href=cover_item.get("href"),
                path=cover_path,
                media_type=cover_item.get("media-type"),
                size_bytes=size,
            )

    return EpubInfo(
        path=epub_path,
        title=title,
        authors=authors,
        language=language,
        package_path=package_path,
        version=version,
        has_cover=cover is not None and cover.path is not None,
        cover=cover,
        is_drm_protected=is_drm_protected(epub_path),
        manifest_count=manifest_count,
        spine_count=spine_count,
        validation=validation,
    )
