from __future__ import annotations

import zipfile

from conftest import write_epub

from epub_cover_surgeon import inspect_epub, is_drm_protected, validate_epub


def test_inspect_reports_metadata_and_cover(minimal_epub):
    info = inspect_epub(minimal_epub)

    assert info.title == "Example Book"
    assert info.authors == ["Example Author"]
    assert info.language == "en"
    assert info.has_cover is True
    assert info.cover.path == "OEBPS/Images/cover.png"
    assert info.manifest_count == 2
    assert info.spine_count == 1
    assert info.validation.ok is True


def test_validate_can_require_cover(no_cover_epub):
    result = validate_epub(no_cover_epub, require_cover=True)

    assert result.ok is False
    assert "No EPUB cover is declared" in result.errors


def test_drm_indicator_detection(tmp_path):
    epub = write_epub(tmp_path / "drm.epub", drm=True)

    assert is_drm_protected(epub) is True
    assert "Common DRM indicator file is present" in validate_epub(epub).warnings


def test_validate_rejects_zip_path_traversal_member(tmp_path):
    epub = write_epub(tmp_path / "unsafe.epub")
    with zipfile.ZipFile(epub, "a") as zf:
        zf.writestr("../outside.txt", "unsafe")

    result = validate_epub(epub)

    assert result.ok is False
    assert any("Unsafe ZIP member path" in error for error in result.errors)
