from __future__ import annotations

import zipfile

from conftest import JPEG_TINY, PNG_1X1

from epub_cover_surgeon import extract_cover, inspect_epub, replace_cover, validate_epub


def test_extract_cover_returns_bytes_and_writes_file(minimal_epub, tmp_path):
    out_dir = tmp_path / "covers"

    extracted = extract_cover(minimal_epub, out_dir)

    assert extracted.data == PNG_1X1
    assert extracted.media_type == "image/png"
    assert (out_dir / "cover.png").read_bytes() == PNG_1X1


def test_replace_cover_updates_manifest_and_archive(minimal_epub, cover_jpg, tmp_path):
    output = tmp_path / "with-new-cover.epub"

    result = replace_cover(minimal_epub, cover_jpg, output)

    assert result.output_path == output
    assert result.validation.ok is True
    info = inspect_epub(output)
    assert info.cover.media_type == "image/jpeg"
    assert info.validation.ok is True
    with zipfile.ZipFile(output) as zf:
        assert zf.read(info.cover.path) == JPEG_TINY
        assert zf.getinfo("mimetype").compress_type == zipfile.ZIP_STORED


def test_replace_cover_adds_cover_to_coverless_epub(no_cover_epub, cover_jpg, tmp_path):
    output = tmp_path / "now-covered.epub"

    replace_cover(no_cover_epub, cover_jpg, output)

    info = inspect_epub(output)
    assert info.has_cover is True
    assert info.cover.media_type == "image/jpeg"
    assert validate_epub(output, require_cover=True).ok is True


def test_replace_cover_can_update_epub_in_place(minimal_epub, cover_jpg):
    result = replace_cover(minimal_epub, cover_jpg)

    assert result.output_path == minimal_epub
    info = inspect_epub(minimal_epub)
    assert info.cover.media_type == "image/jpeg"
    assert validate_epub(minimal_epub, require_cover=True).ok is True
