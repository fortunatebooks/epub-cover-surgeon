# Contributing

Thanks for helping improve EPUB Cover Surgeon.

## Local setup

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```

## Pull request checklist

- Add or update tests for behavior changes.
- Keep cover operations conservative: do not rewrite unrelated book content.
- Do not add network calls or telemetry.
- Do not include copyrighted EPUB fixtures unless they are clearly licensed for redistribution.
- Keep fixture files small; generated fixtures in tests are preferred.
- Explain malformed-EPUB edge cases clearly in the PR description.

## Good first issues

- Add EPUB edge-case fixtures generated from minimal XML.
- Improve validation messages.
- Add docs for distributor-specific cover requirements.
- Add optional image conversion behind an extra dependency.
