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
    "1. Describe Your Study",
    "2. Theory and Measures",
    "3. Check, Register & Export",
    "4. Deposit Data in the STEMEd+ Library",
    "5. Descriptive & Scale Analytics",
    "6. Find Related Data",
]


def _errors(at: AppTest) -> list[str]:
    return [str(e.value) for e in at.exception]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_errors(page):
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not _errors(at), f"start page raised: {_errors(at)}"
    if page != "About this app":
        at.session_state["app_mode"] = page
        at.run()
    assert not _errors(at), f"{page} raised: {_errors(at)}"
    assert at.header, f"{page} rendered no header"
