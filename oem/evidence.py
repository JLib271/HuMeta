# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evidence profiles: how an instrument's reliability and validity evidence measures up to the library's rubric.

The rubric (``library/evidence_rubric.json``) has categories (Item reliability, Forms reliability, ... ,
Likert-type item writing validity), each with lettered criteria. An instrument meets a criterion when

* an evidence record implies it (a Cronbach's alpha record meets Item reliability A and B; a test-retest
  record meets Forms reliability C). Guide values in the rubric (alpha > 0.7) are shown next to the reported
  values, not used as pass marks;
* an evidence record lists it in its ``rubric`` tags; or
* the instrument's ``rubric_review`` (a reviewer's checklist with a source) lists it.

No single score is computed: the profile shows which categories have evidence, whether values pass the
rubric's guide values, how many samples, and whether anyone other than the developers has tested it.
Nothing here imports Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from oem.library import Library

#: (evidence_type or statistic name) -> (rubric category, criterion) implied by an evidence record
BY_STATISTIC = {
    "cronbach_alpha": [("item_reliability", "A"), ("item_reliability", "B")],
    "kr20": [("item_reliability", "A"), ("item_reliability", "B")],
    "mcdonald_omega": [("item_reliability", "A")],
    "item_total_correlation": [("item_reliability", "C")],
    "rasch_item_reliability": [("item_reliability", "D")],
    "rasch_person_reliability": [("item_reliability", "E")],
    "spearman_brown": [("forms_reliability", "B")],
    "factor_loading": [("scale_analysis", "B")],
}
BY_TYPE = {
    "alternate_forms": [("forms_reliability", "A")],
    "split_half": [("forms_reliability", "B")],
    "test_retest": [("forms_reliability", "C")],
    "item_fit": [("item_analysis", "D")],
    "readability": [("cultural", "A")],
    "item_bias": [("cultural", "C")],
    "measurement_invariance": [("cultural", "C")],
    "factor_structure": [("scale_analysis", "A")],
    "expert_review": [("post_item_content", "A")],
    "known_groups": [("criterion_construct", "B")],
    "relations_to_other_variables": [("criterion_construct", "C")],
}
#: evidence types that belong to the rubric only through explicit tags (they say which criterion)
TAG_ONLY = {"item_analysis", "response_process", "test_content", "irt_scaling"}
#: reliability evidence the rubric does not score (it was written for tests and surveys, not observation protocols)
OTHER_RELIABILITY = {"inter_rater"}

MC_TYPES = {"multiple_choice", "multiple_response", "dichotomous", "single_response"}
LIKERT_TYPES = {"likert", "rating_scale"}

KIND_LABELS = {"reliability": "Reliability", "validity": "Validity", "item_writing": "Item writing"}


@dataclass
class Criterion:
    id: str
    label: str
    approach: str | None
    threshold: dict | None
    status: str = "none"  # met | partly | not_met | none
    detail: str = ""
    sources: list[str] = field(default_factory=list)
    values: list[tuple[float, bool, str]] = field(default_factory=list)  # (value, passes, part)


@dataclass
class Category:
    id: str
    numeral: str
    label: str
    kind: str
    description: str
    applies: bool
    criteria: list[Criterion]

    @property
    def reported(self) -> bool:
        return any(c.status in ("met", "partly") for c in self.criteria)

    @property
    def met_letters(self) -> list[str]:
        return [c.id for c in self.criteria if c.status in ("met", "partly")]


@dataclass
class Profile:
    instrument_id: str
    categories: list[Category]
    samples: int
    samples_without_n: int
    independent: int
    independent_unknown: int
    evidence_count: int
    populations: list[str]
    other_evidence: list[dict]
    flags: list[str]

    def coverage(self, kind: str) -> tuple[int, int]:
        cats = [c for c in self.categories if c.kind == kind and c.applies]
        return sum(1 for c in cats if c.reported), len(cats)

    @property
    def other_reliability(self) -> list[dict]:
        return [e for e in self.other_evidence if e.get("evidence_type") in OTHER_RELIABILITY]

    @property
    def tags(self) -> list[str]:
        """Short facet values for search filters."""
        tags = []
        if self.coverage("reliability")[0] or self.other_reliability:
            tags.append("reliability")
        if self.coverage("validity")[0]:
            tags.append("validity")
        if self.independent:
            tags.append("independent")
        if self.samples > 1:
            tags.append("multi_sample")
        return tags


def instrument_formats(inst: dict) -> set[str]:
    """Response formats an instrument uses, for deciding which item-writing categories apply."""
    formats = {(v.get("response_format") or {}).get("type") for v in inst.get("versions", [])}
    formats.discard(None)
    itype = inst.get("instrument_type")
    if itype == "concept_inventory" or (formats & {"mixed"} and itype == "concept_inventory"):
        formats.add("multiple_choice")
    if itype in ("self_report_scale", "attitude_beliefs_survey") and not formats & MC_TYPES:
        formats.add("likert")
    return formats


def _value(stat: dict) -> float | None:
    """The value to judge against a threshold: the lowest value when a range is reported."""
    if stat.get("min") is not None:
        return stat["min"]
    return stat.get("value")


def _sample_key(e: dict) -> tuple:
    src, sm = e.get("source", {}), e.get("sample", {})
    return (src.get("doi") or src.get("citation") or src.get("url") or e["id"], sm.get("n"), sm.get("description"))


def profile(lib: Library, instrument_id: str) -> Profile:
    inst = lib.instrument(instrument_id)
    formats = instrument_formats(inst)
    dims = {d["dimension_id"]: d["name"] for d in inst.get("dimensions", [])}
    cats: dict[str, Category] = {}
    for c in lib.rubric:
        applies = not c.get("applies_to") or bool(formats & set(c["applies_to"]))
        cats[c["id"]] = Category(c["id"], c["numeral"], c["label"], c["kind"], c["description"], applies,
                                 [Criterion(x["id"], x["label"], x.get("approach"), x.get("threshold")) for x in c["criteria"]])

    def crit(cat: str, letter: str) -> Criterion | None:
        category = cats.get(cat)
        return next((x for x in category.criteria if x.id == letter), None) if category else None

    evidence = lib.evidence_for(instrument_id)
    other = []
    for e in evidence:
        stat = e.get("statistic", {})
        implied = list(BY_STATISTIC.get(stat.get("name"), [])) + list(BY_TYPE.get(e.get("evidence_type"), []))
        implied += [(t["category"], t["criterion"]) for t in e.get("rubric", [])]
        if not implied:
            other.append(e)
            continue
        part = dims.get(e.get("dimension_id"), "whole instrument")
        tagged = {(t["category"], t["criterion"]) for t in e.get("rubric", [])}
        for cat, letter in dict.fromkeys(implied):
            c = crit(cat, letter)
            if c is None:
                continue
            c.sources.append(e["id"])
            th = c.threshold
            if not th:
                c.status = "met"
            elif stat.get("name") in th["statistics"] and _value(stat) is not None:
                v = _value(stat)
                c.values.append((v, v > th["above"], part))
            elif (cat, letter) in tagged and c.status == "none":
                c.status = "met"  # a reviewer tagged it (e.g. loadings reported in a note)
                c.detail = "tagged by a reviewer"

    # values: a criterion with a guide value is met when a value was measured; the values are shown, not judged
    for category in cats.values():
        for c in category.criteria:
            if c.threshold and c.values:
                vals = sorted(v for v, _, _ in c.values)
                c.status = "met"
                shown = f"{vals[0]:g}" if len(vals) == 1 else f"{len(vals)} values, {vals[0]:g} to {vals[-1]:g}"
                c.detail = f"{shown}; guide > {c.threshold['above']:g}"

    # reviewer checklist
    for cat, review in (inst.get("rubric_review") or {}).items():
        for letter in review.get("criteria", []):
            c = crit(cat, letter)
            if c and c.status == "none":
                c.status = "met"
                c.detail = c.detail or "from rubric review"
            if c:
                c.sources.append("rubric_review")

    keys = {_sample_key(e) for e in evidence}
    samples_without_n = len({k for k in keys if k[1] is None})
    independent = sum(1 for e in evidence if e.get("source", {}).get("independent") is True)
    independent_unknown = sum(1 for e in evidence if "independent" not in e.get("source", {}))
    pops = sorted({x for e in evidence for x in (e.get("sample", {}).get("education_level"), e.get("sample", {}).get("country")) if x})
    prof = Profile(instrument_id, list(cats.values()), len(keys), samples_without_n, independent, independent_unknown,
                   len(evidence), pops, other, [])

    flags = []
    rel, rel_n = prof.coverage("reliability")
    val, val_n = prof.coverage("validity")
    if not evidence and not inst.get("rubric_review"):
        flags.append("No reliability or validity evidence is recorded yet.")
    else:
        if not rel and prof.other_reliability:
            flags.append("Reliability evidence is inter-rater agreement only, which the rubric does not score.")
        elif not rel:
            flags.append("No reliability evidence recorded.")
        if not val:
            flags.append("No validity evidence recorded.")
    if evidence and not independent and not independent_unknown:
        flags.append("All recorded evidence comes from the instrument's developers; no independent studies yet.")
    if len(keys) == 1:
        flags.append("All recorded evidence comes from a single sample.")
    if samples_without_n:
        flags.append("Some samples have no recorded size.")
    prof.flags = flags
    return prof


def summary_line(prof: Profile) -> str:
    """One line for lists and the app: 'Reliability 2/3 · Validity 3/6 · 4 samples · 0 independent'."""
    rel = prof.coverage("reliability")
    val = prof.coverage("validity")
    parts = [f"Reliability {rel[0]}/{rel[1]}", f"Validity {val[0]}/{val[1]}"]
    iw = prof.coverage("item_writing")
    if iw[1]:
        parts.append(f"Item writing {iw[0]}/{iw[1]}")
    parts.append(f"{prof.samples} sample{'s' if prof.samples != 1 else ''}")
    parts.append(f"{prof.independent} independent")
    return " · ".join(parts)
