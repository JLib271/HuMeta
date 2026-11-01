# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build and export codebooks (data dictionaries).

A codebook lists every variable in a study's dataset: its shared name, label,
type, allowed codes and their labels, missing codes, where it comes from
(library item or standard variable), and how sensitive it is if shared.

Typical use::

    from oem.library import Library
    from oem import codebook

    lib = Library.load()
    variables = [
        *codebook.standard_variable(lib, "participant_id"),
        *codebook.standard_variable(lib, "race_eth"),
        *codebook.instrument_items(lib, "gci", "gci-v4-2014", ["q05", "q01"], timepoint="pre"),
    ]
    book = codebook.Codebook(variables)
    csv_text = book.to_csv()
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass, field

from oem import naming
from oem.library import Library

CODEBOOK_FORMAT = "openedmetadata-codebook"
CODEBOOK_VERSION = 1


@dataclass
class Variable:
    name: str
    label: str
    data_type: str
    values: list[tuple[int, str | None]] = field(default_factory=list)
    missing: list[tuple[int, str | None]] = field(default_factory=list)
    scale_id: str | None = None
    question: str | None = None
    instrument_id: str | None = None
    version_id: str | None = None
    item_id: str | None = None
    option: str | None = None
    standard_variable: str | None = None
    construct_ids: list[str] = field(default_factory=list)
    timepoint: str | None = None
    sensitivity: str = "none"
    notes: str | None = None

    def __post_init__(self) -> None:
        naming.check(self.name)


def _with_timepoint(variables: list[Variable], timepoint: str | None) -> list[Variable]:
    for variable in variables:
        variable.name = naming.with_timepoint(variable.name, timepoint)
        variable.timepoint = timepoint
    return variables


def instrument_items(
    lib: Library,
    instrument_id: str,
    version_id: str,
    item_ids: list[str] | None = None,
    timepoint: str | None = None,
) -> list[Variable]:
    """Variables for library items (all items of the version if ``item_ids`` is None).

    Single-response items become one variable coded 1..n for options A..E.
    Select-all items become one 0/1 variable per option. Item text is included
    only when the instrument's license allows it; answer keys are never included.
    """
    prefix = lib.prefix(instrument_id)
    text_ok = lib.item_text_allowed(instrument_id)
    all_items = lib.items(instrument_id, version_id)
    if item_ids is None:
        chosen = all_items
    else:
        by_id = {item["item_id"]: item for item in all_items}
        missing = [i for i in item_ids if i not in by_id]
        if missing:
            raise KeyError(f"Items not in {instrument_id}/{version_id}: {', '.join(missing)}")
        chosen = [by_id[i] for i in item_ids]
    default_missing = list(lib.scale("selected").missing) if "selected" in lib.scales else []
    variables: list[Variable] = []
    for item in chosen:
        base = naming.item_variable(prefix, item["item_id"])
        question = item.get("stem") if text_ok else None
        label = f"{instrument_id} {version_id} item {item['number']}"
        common = dict(
            instrument_id=instrument_id,
            version_id=version_id,
            item_id=item["item_id"],
            construct_ids=list(item.get("construct_ids", [])),
            question=question,
        )
        options = item.get("options", [])
        if item.get("scale_id"):
            scale = lib.scale(item["scale_id"])
            variables.append(Variable(name=base, label=label, data_type="ordinal" if scale.level == "ordinal" else "categorical",
                                      values=list(scale.points), missing=list(scale.missing), scale_id=scale.id, **common))
        elif item.get("response_type") == "multiple_response":
            selected = lib.scale("selected")
            for option in options:
                option_label = option["label"]
                text = option.get("text") if text_ok else None
                variables.append(Variable(
                    name=naming.option_variable(base, option_label),
                    label=f"{label}, option {option_label}" + (f": {text}" if text else ""),
                    data_type="binary", values=list(selected.points), missing=list(selected.missing),
                    scale_id="selected", option=option_label, **common))
        else:
            values = []
            for code, option in enumerate(options, start=1):
                text = option.get("text") if text_ok else None
                values.append((code, f"{option['label']}: {text}" if text else option["label"]))
            variables.append(Variable(name=base, label=label, data_type="categorical", values=values,
                                      missing=default_missing, **common))
    return _with_timepoint(variables, timepoint)


def standard_variable(lib: Library, name: str, timepoint: str | None = None) -> list[Variable]:
    """Variables for a standard variable (several for select-all questions)."""
    spec = lib.standard_variable(name)
    sensitivity = spec["sensitivity"]
    missing = list(lib.scale("selected").missing) if "selected" in lib.scales else []
    common = dict(standard_variable=name, sensitivity=sensitivity, question=spec.get("question"), notes=spec.get("notes"))
    if spec["data_type"] == "select_all":
        selected = lib.scale("selected")
        variables = [
            Variable(name=naming.check(f"{name}_{option['suffix']}"), label=f"{spec['label']}: {option['label']}",
                     data_type="binary", values=list(selected.points), missing=list(selected.missing),
                     scale_id="selected", option=option["label"], **common)
            for option in spec["options"]
        ]
    elif spec.get("scale_id"):
        scale = lib.scale(spec["scale_id"])
        variables = [Variable(name=name, label=spec["label"], data_type="categorical", values=list(scale.points),
                              missing=list(scale.missing), scale_id=scale.id, **common)]
    elif spec.get("options"):
        variables = [Variable(name=name, label=spec["label"], data_type="categorical",
                              values=[(o["code"], o["label"]) for o in spec["options"]], missing=missing, **common)]
    else:
        variables = [Variable(name=name, label=spec["label"], data_type=spec["data_type"], missing=missing, **common)]
    return _with_timepoint(variables, timepoint)


class Codebook:
    """An ordered, name-unique set of variables with export helpers."""

    COLUMNS = (
        "name", "label", "data_type", "values", "missing", "scale_id", "question",
        "instrument_id", "version_id", "item_id", "option", "standard_variable",
        "construct_ids", "timepoint", "sensitivity", "notes",
    )

    def __init__(self, variables: list[Variable]):
        names = [v.name for v in variables]
        duplicates = sorted({n for n in names if names.count(n) > 1})
        if duplicates:
            raise naming.NamingError(f"Duplicate variable names: {', '.join(duplicates)}")
        self.variables = list(variables)

    def __len__(self) -> int:
        return len(self.variables)

    def names(self) -> list[str]:
        return [v.name for v in self.variables]

    def sensitive(self) -> list[Variable]:
        """Variables that need review or removal before data are shared."""
        return [v for v in self.variables if v.sensitivity != "none"]

    @staticmethod
    def _codes(pairs: list[tuple[int, str | None]]) -> str:
        return "; ".join(f"{code}={label}" if label else str(code) for code, label in pairs)

    def to_rows(self) -> list[dict]:
        rows = []
        for v in self.variables:
            row = asdict(v)
            row["values"] = self._codes(v.values)
            row["missing"] = self._codes(v.missing)
            row["construct_ids"] = "; ".join(v.construct_ids)
            rows.append({column: ("" if row[column] is None else row[column]) for column in self.COLUMNS})
        return rows

    def to_csv(self) -> str:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=self.COLUMNS)
        writer.writeheader()
        writer.writerows(self.to_rows())
        return buffer.getvalue()

    def to_json(self) -> str:
        variables = []
        for v in self.variables:
            record = asdict(v)
            record["values"] = [{"code": c, "label": l} for c, l in v.values]
            record["missing"] = [{"code": c, "label": l} for c, l in v.missing]
            variables.append({k: val for k, val in record.items() if val not in (None, [], "")})
        return json.dumps({"format": CODEBOOK_FORMAT, "version": CODEBOOK_VERSION, "variables": variables},
                          ensure_ascii=False, indent=2)
