# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared variable-naming rules.

Researchers do not type variable names; the app generates them from the
library so every study that uses the same item, scale, or standard variable
ends up with the same column name. That is what lets datasets from different
studies be combined and lets Module 4 match columns automatically.

Rules
-----
* Lowercase letters, digits and underscores; starts with a letter.
* At most 32 characters, so names work in Stata (32), SPSS (64), R and Python.
* Library items:          ``<instrument prefix>_<item_id>``   e.g. ``gci_q05``
* Select-all options:     ``<item variable>_<option>``        e.g. ``gci_q01_c``
* Standard variables:     fixed names from ``library/standard_variables.json``
* Custom variables:       ``<construct>_<nn>``                e.g. ``belong_01``
* Repeated measures:      ``<name>_<timepoint>``              e.g. ``gci_q05_pre``
"""

from __future__ import annotations

import re

MAX_LENGTH = 32
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,31}$")

#: Timepoint suffixes for wide-format repeated-measures data.
TIMEPOINT_SUFFIXES = ("pre", "post", "mid", "fu", "t1", "t2", "t3", "t4", "t5", "t6")

#: Names reserved by common statistics packages or by this convention.
RESERVED = frozenset({"_n", "_all", "if", "in", "by", "and", "or", "not", "with", "to", "all", "eq", "ne", "lt", "le", "gt", "ge"})


class NamingError(ValueError):
    """Raised when a variable name cannot be generated or is invalid."""


def problems(name: str) -> list[str]:
    """Return a list of reasons ``name`` breaks the naming rules (empty if valid)."""
    issues = []
    if not name:
        return ["name is empty"]
    if len(name) > MAX_LENGTH:
        issues.append(f"longer than {MAX_LENGTH} characters ({len(name)})")
    if not NAME_PATTERN.match(name[:MAX_LENGTH]):
        issues.append("must start with a lowercase letter and use only a-z, 0-9 and _")
    if "__" in name:
        issues.append("must not contain double underscores")
    if name.endswith("_"):
        issues.append("must not end with an underscore")
    if name in RESERVED:
        issues.append("is a reserved word")
    return issues


def is_valid(name: str) -> bool:
    return not problems(name)


def check(name: str) -> str:
    """Return ``name`` unchanged if valid, otherwise raise :class:`NamingError`."""
    issues = problems(name)
    if issues:
        raise NamingError(f"Invalid variable name {name!r}: " + "; ".join(issues))
    return name


def slugify(text: str, max_length: int = 12) -> str:
    """Turn free text into a short name fragment: 'Sense of Belonging' -> 'sense_of_bel'."""
    fragment = re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")
    fragment = re.sub(r"_+", "_", fragment)[:max_length].rstrip("_")
    if not fragment or not fragment[0].isalpha():
        fragment = ("v_" + fragment).rstrip("_") if fragment else "v"
    return fragment


def item_variable(prefix: str, item_id: str) -> str:
    """Name for one library item, e.g. ('gci', 'q05') -> 'gci_q05'."""
    return check(f"{prefix}_{item_id.replace('-', '_').lower()}")


def option_variable(base: str, option_label: str) -> str:
    """Name for one option of a select-all-that-apply item, e.g. ('gci_q01', 'C') -> 'gci_q01_c'."""
    return check(f"{base}_{slugify(option_label, 8)}")


def custom_variable(construct: str, number: int) -> str:
    """Name for a researcher-written item, e.g. ('belonging', 1) -> 'belonging_01'."""
    if number < 1:
        raise NamingError("custom variable numbers start at 1")
    return check(f"{slugify(construct, 12)}_{number:02d}")


def with_timepoint(name: str, timepoint: str | None) -> str:
    """Append a timepoint suffix for wide-format repeated measures."""
    if not timepoint:
        return check(name)
    if timepoint not in TIMEPOINT_SUFFIXES:
        raise NamingError(f"unknown timepoint {timepoint!r}; use one of {', '.join(TIMEPOINT_SUFFIXES)}")
    return check(f"{name}_{timepoint}")


def deduplicate(names: list[str]) -> list[str]:
    """Make names unique by appending _2, _3 ... (keeps order, never exceeds the length limit)."""
    seen: dict[str, int] = {}
    result = []
    for name in names:
        if name not in seen:
            seen[name] = 1
            result.append(name)
            continue
        seen[name] += 1
        suffix = f"_{seen[name]}"
        candidate = name[: MAX_LENGTH - len(suffix)] + suffix
        while candidate in seen:
            seen[name] += 1
            suffix = f"_{seen[name]}"
            candidate = name[: MAX_LENGTH - len(suffix)] + suffix
        seen[candidate] = 1
        result.append(check(candidate))
    return result
