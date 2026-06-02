# EPUB Cover Surgeon

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**EPUB Cover Surgeon** is a tiny, dependency-free CLI and Python library for extracting, replacing, inspecting, validating, and lightly hardening EPUB cover images.

It is designed for indie authors, ebook developers, archives, small publishers, QA scripts, and build pipelines that need a focused EPUB-cover tool without opening a full publishing suite.

## Highlights

- Extract the declared cover image from an EPUB.
- Insert or replace cover images while preserving existing book files and metadata.
- Inspect title, author, language, cover status, manifest size, spine size, and basic validation status.
- Detect common DRM indicator files (`META-INF/encryption.xml`, `META-INF/rights.xml`).
- Validate basic EPUB structure before and after modifications.
- Apply safe ZIP handling to avoid path traversal and obvious archive bombs.
- Run as either `epub-cover` or `epub-cover-surgeon`.
- Use as a Python library with dataclass return values.
- Install and deploy in seconds: no runtime dependencies beyond Python 3.10+.

## Installation

```bash
pip install epub-cover-surgeon
```

Until the package is published, install directly from a checkout:

```bash
cd epub-cover-surgeon
python -m pip install .
```

For development:

```bash
python -m pip install -e '.[dev]'
pytest
```

## Quick start

```bash
# Inspect metadata and cover status
epub-cover inspect book.epub

# Extract the declared cover image
epub-cover extract book.epub --out cover.jpg

# Replace or insert a cover image
epub-cover replace book.epub new-cover.jpg --out book-with-cover.epub

# Validate basic EPUB structure
epub-cover validate book-with-cover.epub --require-cover

# Write a validated copy and optionally replace the cover
epub-cover harden book.epub --cover new-cover.jpg --out book-retail-safe.epub
```

JSON output is available for automation:

```bash
epub-cover --json inspect book.epub
```

Example inspection output:

```text
Title: Alice's Adventures in Wonderland
Author: Lewis Carroll
Language: en
Package: OEBPS/content.opf
EPUB version: 3.0
Cover: present
Cover path: OEBPS/Images/cover.jpg
Cover type: image/jpeg
DRM: not detected
Manifest items: 18
Spine items: 12
Validation: passed
```

## Python API

```python
from epub_cover_surgeon import extract_cover, inspect_epub, replace_cover, validate_epub

info = inspect_epub("book.epub")
print(info.title, info.authors, info.has_cover)

cover = extract_cover("book.epub", "cover-output/")
print(cover.media_type, cover.filename)

result = replace_cover("book.epub", "new-cover.jpg", "book-with-cover.epub")
assert result.validation.ok

validation = validate_epub("book-with-cover.epub", require_cover=True)
print(validation.ok, validation.errors)
```

## What the tool changes

`replace` and `harden --cover` are intentionally conservative:

1. Open the EPUB as a ZIP archive.
2. Run safety checks before reading members.
3. Read `META-INF/container.xml` and the referenced OPF package document.
4. Locate the current cover by:
   - EPUB 2 metadata: `<meta name="cover" content="...">`
   - EPUB 3 manifest property: `properties="cover-image"`
   - a conservative fallback image item whose id or href includes `cover`
5. Update or add a cover manifest item.
6. Ensure EPUB 2 cover metadata is present.
7. Copy the EPUB to the output path while replacing only the OPF document and cover image.
8. Keep the `mimetype` entry first and uncompressed when rewriting.
9. Validate the output.

It does **not** rewrite chapter XHTML, normalize all links, reflow text, edit CSS, convert image formats, or remove DRM.

## Safety model

EPUB files are ZIP archives, so the library rejects common dangerous structures before processing:

- absolute ZIP member paths
- `..` path traversal entries
- excessive entry counts
- excessive total uncompressed size
- oversized individual entries
- non-ZIP files renamed to `.epub`

DRM detection is intentionally simple and non-invasive. The tool reports common indicator files, but it does not bypass, remove, or weaken DRM.

## CLI reference

### `inspect`

```bash
epub-cover inspect book.epub
epub-cover --json inspect book.epub
```

### `extract`

```bash
epub-cover extract book.epub --out cover.jpg
epub-cover extract book.epub --out covers/
```

If `--out` is a directory, the original cover filename from the EPUB is used.

### `replace`

```bash
epub-cover replace book.epub cover.jpg --out book-with-cover.epub
```

Supported cover media types are inferred from common image extensions: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, and `.svg`.

### `validate`

```bash
epub-cover validate book.epub
epub-cover validate book.epub --require-cover
```

### `harden`

```bash
epub-cover harden book.epub --out clean-copy.epub
epub-cover harden book.epub --cover cover.jpg --out retail-copy.epub --require-cover
```

## Repository layout

```text
epub-cover-surgeon/
  src/epub_cover_surgeon/
    cli.py          # argparse CLI
    cover.py        # extract and replace cover operations
    harden.py       # conservative hardening entry point
    inspect.py      # inspection API
    metadata.py     # container.xml and OPF helpers
    models.py       # dataclass result objects
    validate.py     # basic EPUB validation and DRM indicators
    zip_safety.py   # ZIP safety checks
  tests/            # pytest suite with generated EPUB fixtures
  examples/         # small automation examples
```

## Development

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
python -m build
```

## Roadmap

- More compatibility checks for distributor-specific EPUB requirements.
- Optional image format conversion through an extra dependency group.
- Repair mode for broken cover references.
- Fixture corpus of public-domain EPUB edge cases.
- Richer JSON diagnostics explaining exactly which EPUB structures were changed.

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and the issue templates before opening a PR.

## License

MIT. See [LICENSE](LICENSE).
