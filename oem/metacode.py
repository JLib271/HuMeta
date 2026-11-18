# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""HuMeta metadata codes: Construct_Measure_Item_Target.

Every variable in a codebook gets a metadata code built from the same parts in
every study, so studies can be matched at each level:

* **Construct**: ``outcome_expectations_SCT`` (the theory's construct, tagged
  with the theory), the shared construct's id (``self_efficacy``) for a
  construct taken from the shared list, or the researcher's own name.
* **Construct_Measure**: ``outcome_expectations_SCT_Smith2017``. A library
  instrument is named by the first author and year of its original citation;
  researcher-written questions are ``Own``; codes in a coding scheme are ``Codes``.
* **Construct_Measure_Item**: ``..._Smith2017_item1_PeopleExpectMeTo``. The item's
  number, then its first words when the item text may be shown (otherwise the
  number only).
* **Construct_Measure_Item_Target**: ``..._item1_PeopleExpectMeTo_Vote``, when the
  researcher names what the measure is about (its target).

The code is metadata, kept beside the data column name: column names stay short
(at most 32 characters) so every statistics package can read them.
"""

from __future__ import annotations

import re

from oem.library import Library

OWN_MEASURE = "Own"
CODES_MEASURE = "Codes"
ITEM_WORDS = 4
TARGET_WORDS = 3


def _snake(text: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(text).lower())).strip("_")


def camel(text: str, words: int) -> str:
    """'People expect me to vote' -> 'PeopleExpectMeTo' (first ``words`` words, letters and digits only)."""
    parts = re.findall(r"[A-Za-z0-9]+", str(text or ""))[:words]
    return "".join(p[:1].upper() + p[1:] for p in parts)


def framework_tag(lib: Library, framework_id: str) -> str:
    """The theory's short name: the abbreviation in its label, '(SCT)' -> 'SCT', else its id in capitals."""
    label = (lib.frameworks.get(framework_id) or {}).get("label", "")
    match = re.search(r"\(([A-Z][A-Za-z0-9-]{1,11})\)", label)
    return (match.group(1) if match else framework_id).replace("-", "").upper() if framework_id else ""


def construct_code(lib: Library, construct: dict) -> str:
    """Construct level: the theory's construct with the theory's tag, else the shared construct, else the name."""
    framework_id = construct.get("framework_id")
    if framework_id and "." in construct.get("id", ""):
        return f"{construct['id'].split('.', 1)[1]}_{framework_tag(lib, framework_id)}"
    if construct.get("shared_construct_id"):
        return construct["shared_construct_id"]
    return _snake(construct.get("label") or construct.get("id", "construct")) or "construct"


def instrument_code(lib: Library, instrument_id: str) -> str:
    """A library instrument as first author and year of its original citation: 'Pintrich1991'.

    Falls back to the instrument's id when the citation has no 'Surname, ... (Year)'.
    """
    inst = lib.instruments.get(instrument_id) or {}
    text = (inst.get("original_citation") or {}).get("text") or ""
    author = re.match(r"\s*([A-Za-z][A-Za-z'\-]+)", text)
    year = re.search(r"\((\d{4})[a-z]?\)", text) or re.search(r"\b(1[89]\d\d|20\d\d)\b", text)
    if author and year:
        return camel(author.group(1), 1) + year.group(1)
    return camel(instrument_id.replace("-", " "), 6) or instrument_id


def measure_code(lib: Library, measure: dict) -> str:
    """Measure level part: the instrument's author-year, 'Own' for written questions, 'Codes' for codes."""
    if measure.get("kind") == "instrument" and measure.get("instrument_id"):
        return instrument_code(lib, measure["instrument_id"])
    return CODES_MEASURE if measure.get("kind") == "code" else OWN_MEASURE


def item_code(number: int | str, text: str | None = None) -> str:
    """Item level part: 'item1_PeopleExpectMeTo', or 'item1' when the text may not be shown."""
    words = camel(text or "", ITEM_WORDS)
    return f"item{number}" + (f"_{words}" if words else "")


def target_code(target: str | None) -> str:
    """Target part: 'voting' -> 'Voting', 'Vote in elections' -> 'VoteInElections'."""
    return camel(target or "", TARGET_WORDS)


def join(*parts: str) -> str:
    return "_".join(p for p in parts if p)


def level(measure: bool = False, item: bool = False, target: bool = False) -> str:
    """Which parts a code has, e.g. 'construct_measure_item_target' or 'construct_measure_target'."""
    return join("construct", "measure" if measure else "", "item" if item else "", "target" if target else "")
