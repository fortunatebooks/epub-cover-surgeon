"""Example: inspect an EPUB, then replace its cover if needed.

Run from a checkout with:

    python examples/inspect_and_replace.py book.epub cover.jpg output.epub
"""

from __future__ import annotations

import sys
from pathlib import Path

from epub_cover_surgeon import inspect_epub, replace_cover


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: python examples/inspect_and_replace.py INPUT.epub COVER_IMAGE OUTPUT.epub")
        return 2

    input_epub = Path(sys.argv[1])
    cover = Path(sys.argv[2])
    output_epub = Path(sys.argv[3])

    info = inspect_epub(input_epub)
    print(f"{info.title or input_epub.name}: cover {'present' if info.has_cover else 'missing'}")

    result = replace_cover(input_epub, cover, output_epub)
    print(f"Wrote {result.output_path}; validation ok={result.validation.ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
