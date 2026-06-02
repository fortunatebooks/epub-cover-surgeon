"""Cover extraction and replacement."""

from __future__ import annotations

import mimetypes
import posixpath
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from .metadata import (
    OPF_NS,
    ensure_metadata_and_manifest,
    find_cover_item,
    open_epub,
    read_package_document,
    set_cover_meta,
)
from .models import CoverInfo, ExtractedCover, ReplacementResult
from .validate import validate_epub
from .zip_safety import normalize_zip_path

_IMAGE_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


def guess_image_media_type(path: str | Path) -> str:
    """Guess image media type from extension, falling back to mimetypes."""

    suffix = Path(path).suffix.lower()
    return _IMAGE_TYPES.get(suffix) or mimetypes.guess_type(str(path))[0] or "application/octet-stream"


def _cover_extension(media_type: str, fallback_path: str | Path | None = None) -> str:
    if media_type == "image/jpeg":
        return ".jpg"
    for suffix, candidate in _IMAGE_TYPES.items():
        if candidate == media_type and suffix != ".jpeg":
            return suffix
    if fallback_path:
        suffix = Path(fallback_path).suffix.lower()
        if suffix:
            return suffix
    return ".img"


def extract_cover(path: str | Path, out: str | Path | None = None) -> ExtractedCover:
    """Extract the declared EPUB cover image.

    Raises:
        ValueError: if the EPUB does not declare a readable cover.
    """

    with open_epub(path) as epub_zip:
        package = read_package_document(epub_zip)
        cover_item, _cover_id, cover_path = find_cover_item(package)
        if cover_item is None or not cover_path:
            raise ValueError("EPUB does not declare a cover image")
        try:
            data = epub_zip.read(cover_path)
        except KeyError as exc:
            raise ValueError(f"Declared cover image is missing: {cover_path}") from exc

        media_type = cover_item.get("media-type") or guess_image_media_type(cover_path)
        filename = Path(cover_path).name or f"cover{_cover_extension(media_type)}"
        extracted = ExtractedCover(
            data=data,
            media_type=media_type,
            filename=filename,
            source_path=cover_path,
        )

    if out is not None:
        output = Path(out)
        if output.is_dir() or (not output.exists() and output.suffix == ""):
            output = output / filename
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)

    return extracted


def _next_cover_path(package_path: str, media_type: str) -> tuple[str, str]:
    base_dir = str(Path(package_path).parent).replace(".", "", 1).strip("/")
    href = f"Images/cover{_cover_extension(media_type)}"
    archive_path = normalize_zip_path(posixpath.join(base_dir, href) if base_dir else href)
    return href, archive_path


def _copy_archive_with_replacements(
    source: Path,
    output: Path,
    replacements: dict[str, bytes],
    skipped: set[str] | None = None,
) -> None:
    skipped = skipped or set()
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_output = output.with_suffix(output.suffix + ".tmp")
    if temp_output.exists():
        temp_output.unlink()

    with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(temp_output, "w") as zout:
        names_written: set[str] = set()

        if "mimetype" in zin.namelist():
            zout.writestr(
                zipfile.ZipInfo("mimetype"),
                zin.read("mimetype"),
                compress_type=zipfile.ZIP_STORED,
            )
            names_written.add("mimetype")

        for item in zin.infolist():
            if item.filename in names_written or item.filename in skipped or item.filename in replacements:
                continue
            data = zin.read(item.filename)
            zout.writestr(item, data)
            names_written.add(item.filename)

        for name, data in replacements.items():
            if name in names_written:
                continue
            compress_type = zipfile.ZIP_STORED if name == "mimetype" else zipfile.ZIP_DEFLATED
            zout.writestr(name, data, compress_type=compress_type)
            names_written.add(name)

    temp_output.replace(output)


def replace_cover(
    epub_path: str | Path,
    cover_image_path: str | Path,
    output_path: str | Path | None = None,
    *,
    cover_title: str = "Cover",
) -> ReplacementResult:
    """Insert or replace an EPUB cover image while preserving other files."""

    source = Path(epub_path)
    cover_image = Path(cover_image_path)
    if not cover_image.is_file():
        raise FileNotFoundError(f"Cover image file not found: {cover_image}")
    if cover_image.stat().st_size == 0:
        raise ValueError("Cover image file is empty")
    media_type = guess_image_media_type(cover_image)
    if not media_type.startswith("image/"):
        raise ValueError(f"Unsupported cover media type: {media_type}")

    output = Path(output_path) if output_path is not None else source
    working_source = source
    if output.resolve() == source.resolve():
        working_source = source.with_name(f"{source.name}.bak-for-cover-replace.epub")
        shutil.copy2(source, working_source)

    skipped: set[str] = set()
    try:
        with open_epub(working_source) as epub_zip:
            package = read_package_document(epub_zip)
            metadata, manifest = ensure_metadata_and_manifest(package.root)
            cover_item, _cover_id, old_cover_path = find_cover_item(package)
            cover_id = "cover-image"

            if cover_item is None:
                cover_href, cover_archive_path = _next_cover_path(package.path, media_type)
                cover_item = ET.SubElement(
                    manifest,
                    f"{{{OPF_NS}}}item",
                    {
                        "id": cover_id,
                        "href": cover_href,
                        "media-type": media_type,
                        "properties": "cover-image",
                    },
                )
            else:
                cover_id = cover_item.get("id") or cover_id
                cover_href = cover_item.get("href") or _next_cover_path(package.path, media_type)[0]
                if Path(cover_href).suffix.lower() not in _IMAGE_TYPES:
                    cover_href, _unused = _next_cover_path(package.path, media_type)
                cover_archive_path = normalize_zip_path(
                    posixpath.join(str(Path(package.path).parent).replace(".", "", 1).strip("/"), cover_href)
                    if str(Path(package.path).parent).replace(".", "", 1).strip("/")
                    else cover_href
                )
                cover_item.set("id", cover_id)
                cover_item.set("href", cover_href)
                cover_item.set("media-type", media_type)
                properties = set((cover_item.get("properties") or "").split())
                properties.add("cover-image")
                cover_item.set("properties", " ".join(sorted(properties)))

            cover_item.set("id", cover_id)
            set_cover_meta(metadata, cover_id)

            # EPUB 2 readers often also look at the guide cover reference.
            guide = package.root.find(f"{{{OPF_NS}}}guide")
            if guide is None:
                guide = package.root.find("guide")
            if guide is not None and not any((ref.get("type") or "").lower() == "cover" for ref in list(guide)):
                ET.SubElement(guide, f"{{{OPF_NS}}}reference", {"type": "cover", "title": cover_title, "href": cover_item.get("href", "")})

            opf_bytes = ET.tostring(package.root, encoding="utf-8", xml_declaration=True)
            replacements = {
                package.path: opf_bytes,
                cover_archive_path: cover_image.read_bytes(),
            }
            if old_cover_path and old_cover_path != cover_archive_path:
                skipped.add(old_cover_path)

        _copy_archive_with_replacements(working_source, output, replacements, skipped)
    finally:
        if working_source != source:
            working_source.unlink(missing_ok=True)

    validation = validate_epub(output, require_cover=True)
    if not validation.ok:
        raise ValueError("EPUB cover replacement produced invalid output: " + "; ".join(validation.errors))

    cover_info = CoverInfo(
        item_id=cover_id,
        href=cover_href,
        path=cover_archive_path,
        media_type=media_type,
        size_bytes=cover_image.stat().st_size,
    )
    return ReplacementResult(output_path=output, validation=validation, cover=cover_info)
