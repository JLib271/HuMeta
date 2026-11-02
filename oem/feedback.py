# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tester feedback: turn a message typed in the app into a GitHub issue.

The app's "Send feedback" box (bottom of every page) calls :func:`build_issue`
and files the result as an issue in the project's repository, so testers need
no GitHub account. Each issue is labeled ``feedback``, with its kind and the
page it came from, so maintainers (and later the governance committee) can sort
it. Nothing from the tester's project file is included.

Nothing here imports Streamlit.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: kind of feedback -> (label shown in the app, GitHub label)
KINDS: dict[str, tuple[str, str]] = {
    "confusing": ("Something is confusing or unclear", "feedback: confusing"),
    "broken": ("Something is broken or shows an error", "feedback: bug"),
    "field": ("Something is missing for my field", "feedback: my field"),
    "idea": ("An idea or suggestion", "feedback: idea"),
    "praise": ("Something works well", "feedback: works well"),
    "other": ("Something else", "feedback: other"),
}
FEEDBACK_LABEL = "feedback"
LABEL_COLORS = {FEEDBACK_LABEL: "0e8a16", "page": "c5def5", "kind": "fbca04"}
MIN_LENGTH = 10
MAX_LENGTH = 5000
MAX_PER_SESSION = 10


@dataclass
class Issue:
    title: str
    body: str
    labels: list[str]


def label_color(label: str) -> str:
    if label == FEEDBACK_LABEL:
        return LABEL_COLORS[FEEDBACK_LABEL]
    return LABEL_COLORS["page"] if label.startswith("page:") else LABEL_COLORS["kind"]


def page_label(page: str) -> str:
    """GitHub label for an app page, e.g. '2. Framework and Measures' -> 'page: module 2'."""
    match = re.match(r"\s*(\d+)\.", page or "")
    return f"page: module {match.group(1)}" if match else "page: about"


def problems(kind: str, message: str) -> list[str]:
    out = []
    if kind not in KINDS:
        out.append("Choose what kind of feedback this is.")
    text = (message or "").strip()
    if len(text) < MIN_LENGTH:
        out.append(f"Write at least {MIN_LENGTH} characters.")
    if len(text) > MAX_LENGTH:
        out.append(f"Keep it under {MAX_LENGTH} characters (or send it in two parts).")
    return out


def _one_line(text: str, limit: int) -> str:
    line = re.sub(r"\s+", " ", text or "").strip()
    return line if len(line) <= limit else line[: limit - 1].rstrip() + "…"


def build_issue(kind: str, page: str, message: str, name: str | None = None, field: str | None = None,
                signed_in_as: str | None = None) -> Issue:
    """The GitHub issue for one piece of feedback. Raises ValueError if the input has problems."""
    found = problems(kind, message)
    if found:
        raise ValueError(" ".join(found))
    kind_label, kind_tag = KINDS[kind]
    who = (signed_in_as or "").strip() or _one_line(name or "", 80) or "Anonymous tester"
    lines = [
        "### Tester feedback from the HuMeta Portal",
        "",
        f"* **Page:** {page}",
        f"* **Kind:** {kind_label}",
        f"* **From:** {who}" + (" (signed in)" if (signed_in_as or "").strip() else ""),
    ]
    if (field or "").strip():
        lines.append(f"* **Tester's field:** {_one_line(field, 120)}")
    lines += ["", "#### Feedback", "", message.strip(), "", "---",
              "_Filed by the app's feedback box. The tester did not need a GitHub account; reply here and "
              "share the answer with them directly if they left a name._"]
    title = f"[{page_label(page).removeprefix('page: ').capitalize()}] {_one_line(message, 70)}"
    return Issue(title=title, body="\n".join(lines), labels=[FEEDBACK_LABEL, kind_tag, page_label(page)])
