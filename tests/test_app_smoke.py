"""Smoke test: open every page of the Streamlit app and fail on any exception.

Uses Streamlit's built-in headless test runner (no browser). Skipped when
Streamlit is not installed, so the library tests still run anywhere.
Run with:  python -m pytest tests/test_app_smoke.py -v
"""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parent.parent / "openscience.py")
PAGES = [
    "About this app",
    "1. Study Metadata Schema Registry",
    "2. Variable Instrument Architect",
    "3. Community Data Repository Sync",
    "4. Descriptive & Scale Analytics",
    "5. Published Repository Viewer",
]


def _errors(at: AppTest) -> list[str]:
    return [str(e.value) for e in at.exception]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_errors(page):
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not _errors(at), f"start page raised: {_errors(at)}"
    if page != "About this app":
        at.radio(key="app_mode").set_value(page).run()
    assert not _errors(at), f"{page} raised: {_errors(at)}"
    assert at.header, f"{page} rendered no header"
