# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""HuMeta metadata codes: Construct_Measure_Item_Target.

Every variable in a codebook gets a metadata code built from the same parts in
every study, so studies can be matched at each level:

* **Construct**: ``outcome_expectations_SCT`` (the theory's construct, tagged
  with the theory), the shared construct's id (``self_efficacy``) for a
  construct taken from the shared list, or the researcher's own name.
* **Construct_Measure**: ``outcome_expectations_SCT_Smith2017``. A measure is
  named by the first author and year of its original publication: a library
  instrument by its fixed code in the library (a letter is added if two would
  clash) plus its version's code (``Libarkin2005V4``), a published instrument not in the library from the author and year the
  researcher gives. Researcher-written questions are ``Own``; codes in a coding
  scheme are ``Codes``.
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


def author_year(text: str | None) -> str:
    """'Smith, J. K. (2017). ...', 'Smith et al. 2017' or 'Smith 2017' -> 'Smith2017' ('' if no surname and year)."""
    author = re.match(r"\s*([A-Za-z][A-Za-z'\-]+)", text or "")
    year = re.search(r"\((\d{4})[a-z]?\)", text or "") or re.search(r"\b(1[89]\d\d|20\d\d)\b", text or "")
    return camel(author.group(1), 1) + year.group(1) if author and year else ""


def instrument_code(lib: Library, instrument_id: str) -> str:
    """A library instrument's fixed code, 'Pintrich1991' (its ``metadata_code`` in the library).

    For a library without fixed codes, worked out from the original citation (first author and
    year), else from the instrument's id.
    """
    inst = lib.instruments.get(instrument_id) or {}
    if inst.get("metadata_code"):
        return inst["metadata_code"]
    return (author_year((inst.get("original_citation") or {}).get("text"))
            or camel(instrument_id.replace("-", " "), 6) or instrument_id)


def version_code(lib: Library, instrument_id: str, version_id: str | None = None) -> str:
    """A library version's fixed code ('V4', 'PhysV3'), added to the instrument's: Libarkin2005V4.

    ``version_id`` defaults to the instrument's first version; '' when the library gives no code.
    """
    versions = (lib.instruments.get(instrument_id) or {}).get("versions") or []
    version = next((v for v in versions if v.get("version_id") == version_id), versions[0] if versions else {})
    return version.get("code") or ""


def measure_code(lib: Library, measure: dict) -> str:
    """Measure level part: the instrument's author-year, 'Own' for written questions, 'Codes' for codes.

    A published instrument that is not in the library is named the same way, from the first author and
    year the researcher gives (``citation``), else from its name.
    """
    if measure.get("kind") == "instrument" and measure.get("instrument_id"):
        return instrument_code(lib, measure["instrument_id"]) + version_code(lib, measure["instrument_id"],
                                                                             measure.get("version_id"))
    if measure.get("kind") == "published":
        return author_year(measure.get("citation")) or camel(measure.get("label") or "", 4) or OWN_MEASURE
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
