"""Safe ZIP helpers for EPUB files.

EPUBs are ZIP archives, so every public entry point validates archive structure
before reading XML or copying members. These checks are intentionally lightweight:
they reject obvious path traversal, absolute paths, oversized archives, and huge
entry counts without trying to be a complete antivirus scanner.
"""

from __future__ import annotations

import posixpath
import zipfile
from pathlib import PurePosixPath

MAX_UNPACKED_MB = 250
MAX_ENTRY_COUNT = 20_000


class ZipSafetyError(ValueError):
    """Raised when an EPUB archive fails safety checks."""


def normalize_zip_path(path: str) -> str:
    """Return a normalized POSIX ZIP member path and reject unsafe paths."""

    normalized = posixpath.normpath(path.replace("\\", "/"))
    if normalized in {"", "."}:
        raise ZipSafetyError("ZIP member path is empty")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts:
        raise ZipSafetyError(f"Unsafe ZIP member path: {path!r}")
    return normalized


def join_zip_path(base_dir: str, href: str) -> str:
    """Join an OPF-relative href to its containing directory safely."""

    if base_dir:
        return normalize_zip_path(posixpath.join(base_dir, href))
    return normalize_zip_path(href)


def check_zip_safety(
    epub_zip: zipfile.ZipFile,
    *,
    filename: str = "EPUB",
    max_unpacked_mb: int = MAX_UNPACKED_MB,
    max_entry_count: int = MAX_ENTRY_COUNT,
) -> None:
    """Reject unsafe ZIP structures before processing an EPUB."""

    infos = epub_zip.infolist()
    if len(infos) > max_entry_count:
        raise ZipSafetyError(
            f"{filename} contains too many archive entries: {len(infos)} (limit: {max_entry_count})"
        )

    max_unpacked_bytes = max_unpacked_mb * 1024 * 1024
    total_unpacked = 0
    for info in infos:
        normalize_zip_path(info.filename)
        total_unpacked += info.file_size
        if info.file_size > max_unpacked_bytes:
            raise ZipSafetyError(
                f"{filename} contains an oversized member: {info.filename} "
                f"({info.file_size} bytes; limit: {max_unpacked_bytes})"
            )

    if total_unpacked > max_unpacked_bytes:
        raise ZipSafetyError(
            f"{filename} is too large when unpacked: {total_unpacked} bytes "
            f"(limit: {max_unpacked_bytes})"
        )
