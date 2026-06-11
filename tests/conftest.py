from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c636000000200015d0b2a0b0000000049454e44ae426082"
)
JPEG_TINY = bytes.fromhex(
    "ffd8ffe000104a46494600010101006000600000ffdb004300030202030202030303"
    "0304030304050805050404050a070706080c0a0c0c0b0a0b0b0d0e12100d0e110e"
    "0b0b1016101113141515150c0f171816141812141514ffdb004301030404050405"
    "09050509140d0b0d14141414141414141414141414141414141414141414141414"
    "141414141414141414141414141414141414141414141414141414141414ffc000"
    "11080001000103012200021101031101ffc4001400010000000000000000000000"
    "0000000000000008ffc40014100100000000000000000000000000000000000000"
    "ffda000c03010002110311003f00b2c001ffd9"
)


def write_epub(path: Path, *, with_cover: bool = True, drm: bool = False) -> Path:
    cover_meta = '<meta name="cover" content="cover-image" />' if with_cover else ""
    cover_item = (
        '<item id="cover-image" href="Images/cover.png" media-type="image/png" properties="cover-image" />'
        if with_cover
        else ""
    )
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:test-book</dc:identifier>
    <dc:title>Example Book</dc:title>
    <dc:creator>Example Author</dc:creator>
    <dc:language>en</dc:language>
    {cover_meta}
  </metadata>
  <manifest>
    {cover_item}
    <item id="chapter" href="Text/chapter.xhtml" media-type="application/xhtml+xml" />
  </manifest>
  <spine>
    <itemref idref="chapter" />
  </spine>
</package>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" /></rootfiles>
</container>""",
        )
        zf.writestr("OEBPS/content.opf", opf)
        zf.writestr(
            "OEBPS/Text/chapter.xhtml",
            "<html xmlns='http://www.w3.org/1999/xhtml'><body><p>Hello.</p></body></html>",
        )
        if with_cover:
            zf.writestr("OEBPS/Images/cover.png", PNG_1X1)
        if drm:
            zf.writestr("META-INF/encryption.xml", "<encryption />")
    return path


@pytest.fixture
def minimal_epub(tmp_path: Path) -> Path:
    return write_epub(tmp_path / "minimal.epub")


@pytest.fixture
def no_cover_epub(tmp_path: Path) -> Path:
    return write_epub(tmp_path / "no-cover.epub", with_cover=False)


@pytest.fixture
def cover_jpg(tmp_path: Path) -> Path:
    path = tmp_path / "new-cover.jpg"
    path.write_bytes(JPEG_TINY)
    return path
