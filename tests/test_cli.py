from __future__ import annotations

import json

from conftest import PNG_1X1

from epub_cover_surgeon.cli import main


def test_cli_inspect_json(minimal_epub, capsys):
    exit_code = main(["--json", "inspect", str(minimal_epub)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["title"] == "Example Book"
    assert payload["has_cover"] is True


def test_cli_validate_failure(no_cover_epub, capsys):
    exit_code = main(["validate", str(no_cover_epub), "--require-cover"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Validation: failed" in captured.out


def test_cli_extract_writes_cover_to_directory(minimal_epub, tmp_path, capsys):
    out_dir = tmp_path / "covers"

    exit_code = main(["extract", str(minimal_epub), "--out", str(out_dir)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert (out_dir / "cover.png").read_bytes() == PNG_1X1
    assert "Extracted image/png cover" in captured.out
