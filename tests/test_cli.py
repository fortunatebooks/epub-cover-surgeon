from __future__ import annotations

import json

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
