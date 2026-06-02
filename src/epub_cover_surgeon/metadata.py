"""EPUB package and metadata parsing helpers."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from .zip_safety import check_zip_safety, join_zip_path, normalize_zip_path

CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("", OPF_NS)
ET.register_namespace("dc", DC_NS)


@dataclass(frozen=True)
class PackageDocument:
    """Parsed EPUB package document (.opf)."""

    path: str
    root: ET.Element
    xml_bytes: bytes

    @property
    def base_dir(self) -> str:
        return str(Path(self.path).parent).replace(".", "", 1).strip("/")


def _find_child(root: ET.Element, name: str) -> ET.Element | None:
    child = root.find(f"{{{OPF_NS}}}{name}")
    if child is not None:
        return child
    return root.find(name)


def find_children(root: ET.Element, name: str) -> list[ET.Element]:
    """Find OPF children with namespace fallback."""

    return list(root.findall(f".//{{{OPF_NS}}}{name}")) or list(root.findall(f".//{name}"))


def read_package_document(epub_zip: zipfile.ZipFile) -> PackageDocument:
    """Read and parse the package document referenced by container.xml."""

    try:
        container_xml = epub_zip.read("META-INF/container.xml")
    except KeyError as exc:
        raise ValueError("EPUB is missing META-INF/container.xml") from exc

    try:
        container = ET.fromstring(container_xml)
    except ET.ParseError as exc:
        raise ValueError(f"container.xml is not valid XML: {exc}") from exc

    rootfile = container.find(f".//{{{CONTAINER_NS}}}rootfile")
    if rootfile is None:
        rootfile = container.find(".//rootfile")
    if rootfile is None:
        raise ValueError("container.xml does not declare a rootfile")

    package_path = rootfile.get("full-path")
    if not package_path:
        raise ValueError("container.xml rootfile is missing full-path")
    package_path = normalize_zip_path(package_path)

    try:
        opf_bytes = epub_zip.read(package_path)
    except KeyError as exc:
        raise ValueError(f"EPUB package document not found: {package_path}") from exc

    try:
        root = ET.fromstring(opf_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"package document is not valid XML: {exc}") from exc

    return PackageDocument(path=package_path, root=root, xml_bytes=opf_bytes)


def open_epub(path: str | Path) -> zipfile.ZipFile:
    """Open an EPUB ZIP archive and run safety checks."""

    epub_path = Path(path)
    if not epub_path.is_file():
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
    if epub_path.suffix.lower() != ".epub":
        raise ValueError(f"Expected an .epub file: {epub_path}")
    if not zipfile.is_zipfile(epub_path):
        raise ValueError(f"Not a valid ZIP/EPUB archive: {epub_path}")

    epub_zip = zipfile.ZipFile(epub_path, "r")
    try:
        check_zip_safety(epub_zip, filename=epub_path.name)
    except Exception:
        epub_zip.close()
        raise
    return epub_zip


def text_values(root: ET.Element, dc_name: str) -> list[str]:
    """Return non-empty Dublin Core text values from a package document."""

    values: list[str] = []
    for element in root.findall(f".//{{{DC_NS}}}{dc_name}") + root.findall(f".//{dc_name}"):
        if element.text and element.text.strip():
            values.append(element.text.strip())
    return values


def manifest_items(root: ET.Element) -> list[ET.Element]:
    return find_children(root, "item")


def spine_itemrefs(root: ET.Element) -> list[ET.Element]:
    return find_children(root, "itemref")


def find_cover_item(package: PackageDocument) -> tuple[ET.Element | None, str | None, str | None]:
    """Return the manifest item used as the cover, its id, and archive path."""

    root = package.root
    cover_id: str | None = None

    for meta in find_children(root, "meta"):
        if (meta.get("name") or "").lower() == "cover" and meta.get("content"):
            cover_id = meta.get("content")
            break

    items = manifest_items(root)
    item: ET.Element | None = None
    if cover_id:
        item = next((candidate for candidate in items if candidate.get("id") == cover_id), None)

    if item is None:
        item = next(
            (
                candidate
                for candidate in items
                if "cover-image" in (candidate.get("properties") or "").split()
            ),
            None,
        )
        if item is not None:
            cover_id = item.get("id")

    if item is None:
        item = next(
            (
                candidate
                for candidate in items
                if (candidate.get("media-type") or "").startswith("image/")
                and "cover" in ((candidate.get("id") or "") + " " + (candidate.get("href") or "")).lower()
            ),
            None,
        )
        if item is not None:
            cover_id = item.get("id")

    if item is None:
        return None, cover_id, None

    href = item.get("href")
    if not href:
        return item, cover_id, None
    return item, cover_id, join_zip_path(package.base_dir, href)


def ensure_metadata_and_manifest(root: ET.Element) -> tuple[ET.Element, ET.Element]:
    """Return package metadata and manifest elements, creating them if needed."""

    metadata = _find_child(root, "metadata")
    if metadata is None:
        metadata = ET.SubElement(root, f"{{{OPF_NS}}}metadata")
    manifest = _find_child(root, "manifest")
    if manifest is None:
        manifest = ET.SubElement(root, f"{{{OPF_NS}}}manifest")
    return metadata, manifest


def set_cover_meta(metadata: ET.Element, cover_id: str) -> None:
    """Set or add the EPUB 2 cover meta entry."""

    for meta in list(metadata):
        if meta.tag.endswith("meta") and (meta.get("name") or "").lower() == "cover":
            meta.set("content", cover_id)
            return
    ET.SubElement(metadata, f"{{{OPF_NS}}}meta", {"name": "cover", "content": cover_id})
