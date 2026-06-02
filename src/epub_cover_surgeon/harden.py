"""Small retail-compatibility hardening helpers."""

from __future__ import annotations

import shutil
from pathlib import Path

from .cover import replace_cover
from .models import ReplacementResult
from .validate import validate_epub


def harden_epub(
    epub_path: str | Path,
    output_path: str | Path,
    *,
    cover_image_path: str | Path | None = None,
    require_cover: bool = False,
) -> ReplacementResult:
    """Create a validated, distribution-friendly copy of an EPUB.

    Today this performs the safe, high-value subset needed by most workflows:
    validate the source archive, optionally insert/replace the cover, ensure the
    resulting archive validates, and write the EPUB mimetype member first and
    uncompressed when a replacement is made. The function is intentionally
    conservative; it does not rewrite book content.
    """

    source_validation = validate_epub(epub_path, require_cover=require_cover and cover_image_path is None)
    if not source_validation.ok:
        raise ValueError("Source EPUB failed validation: " + "; ".join(source_validation.errors))

    if cover_image_path is not None:
        return replace_cover(epub_path, cover_image_path, output_path)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(epub_path, output)
    validation = validate_epub(output, require_cover=require_cover)
    if not validation.ok:
        raise ValueError("Hardened EPUB failed validation: " + "; ".join(validation.errors))
    return ReplacementResult(output_path=output, validation=validation, cover=None)
