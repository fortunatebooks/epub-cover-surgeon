"""Command-line interface for epub-cover-surgeon."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path

from .cover import extract_cover, replace_cover
from .harden import harden_epub
from .inspect import inspect_epub
from .validate import validate_epub


def _json_default(value):
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _print_json(value) -> None:
    print(json.dumps(value, default=_json_default, indent=2, sort_keys=True))


def _print_inspection(info) -> None:
    print(f"Title: {info.title or 'Unknown'}")
    print(f"Author: {', '.join(info.authors) if info.authors else 'Unknown'}")
    print(f"Language: {info.language or 'Unknown'}")
    print(f"Package: {info.package_path or 'Unknown'}")
    print(f"EPUB version: {info.version or 'Unknown'}")
    print(f"Cover: {'present' if info.has_cover else 'missing'}")
    if info.cover:
        print(f"Cover path: {info.cover.path or 'Unknown'}")
        print(f"Cover type: {info.cover.media_type or 'Unknown'}")
    print(f"DRM: {'detected' if info.is_drm_protected else 'not detected'}")
    print(f"Manifest items: {info.manifest_count}")
    print(f"Spine items: {info.spine_count}")
    print(f"Validation: {'passed' if info.validation.ok else 'failed'}")
    for warning in info.validation.warnings:
        print(f"Warning: {warning}")
    for error in info.validation.errors:
        print(f"Error: {error}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="epub-cover",
        description="Extract, replace, inspect, validate, and harden EPUB covers.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON output.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect", help="Inspect EPUB metadata and cover status."
    )
    inspect_parser.add_argument("epub")

    extract_parser = subparsers.add_parser("extract", help="Extract the declared cover image.")
    extract_parser.add_argument("epub")
    extract_parser.add_argument(
        "--out", required=True, help="Output file or directory for the cover image."
    )

    replace_parser = subparsers.add_parser("replace", help="Insert or replace an EPUB cover image.")
    replace_parser.add_argument("epub")
    replace_parser.add_argument("cover")
    replace_parser.add_argument("--out", required=True, help="Output EPUB path.")
    replace_parser.add_argument(
        "--cover-title", default="Cover", help="EPUB 2 guide title for the cover reference."
    )

    validate_parser = subparsers.add_parser("validate", help="Validate basic EPUB structure.")
    validate_parser.add_argument("epub")
    validate_parser.add_argument(
        "--require-cover", action="store_true", help="Fail validation if no cover is declared."
    )

    harden_parser = subparsers.add_parser(
        "harden", help="Write a validated, optionally cover-updated EPUB copy."
    )
    harden_parser.add_argument("epub")
    harden_parser.add_argument("--cover", help="Optional new cover image.")
    harden_parser.add_argument("--out", required=True, help="Output EPUB path.")
    harden_parser.add_argument(
        "--require-cover", action="store_true", help="Require a cover after hardening."
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "inspect":
            info = inspect_epub(args.epub)
            _print_json(info) if args.json else _print_inspection(info)
            return 0 if info.validation.ok else 1

        if args.command == "extract":
            result = extract_cover(args.epub, args.out)
            if args.json:
                _print_json(result)
            else:
                destination = Path(args.out)
                if destination.is_dir() or (not destination.exists() and destination.suffix == ""):
                    destination = destination / result.filename
                print(f"Extracted {result.media_type} cover to {destination}")
            return 0

        if args.command == "replace":
            result = replace_cover(args.epub, args.cover, args.out, cover_title=args.cover_title)
            _print_json(result) if args.json else print(f"Wrote {result.output_path}")
            return 0

        if args.command == "validate":
            result = validate_epub(args.epub, require_cover=args.require_cover)
            if args.json:
                _print_json(result)
            else:
                print("Validation: " + ("passed" if result.ok else "failed"))
                for warning in result.warnings:
                    print(f"Warning: {warning}")
                for error in result.errors:
                    print(f"Error: {error}")
            return 0 if result.ok else 1

        if args.command == "harden":
            result = harden_epub(
                args.epub,
                args.out,
                cover_image_path=args.cover,
                require_cover=args.require_cover,
            )
            _print_json(result) if args.json else print(f"Wrote {result.output_path}")
            return 0

    except Exception as exc:  # noqa: BLE001 - CLI boundary should show clear errors.
        if args.json:
            _print_json({"ok": False, "error": str(exc)})
        else:
            print(f"epub-cover: error: {exc}", file=sys.stderr)
        return 2

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
