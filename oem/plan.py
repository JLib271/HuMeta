# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The variable plan built in Module 2 (Framework and Measures).

A plan runs from theory to data, and each step builds on the one before:

1. ``frameworks``: theories, lenses, the researcher's own framework, or an
   exploratory approach (ids from ``library/frameworks.json``).
2. ``concepts``: what the framework says matters. A framework's concepts are
   copied in, and the researcher can add their own. Each concept may link to a
   construct in ``library/constructs.json``.
3. ``measures``: how each concept is measured or coded. There are three kinds:

   * ``instrument``: a library instrument, optionally one version or subscale
   * ``question``: a researcher-written item
   * ``code``: a code in a coding scheme, for texts, images, media, or interviews

4. ``relationships``: expected links between concepts. They start from the
   framework's paths and the researcher can edit them; the diagram is drawn
   from them.

From a plan you can build a :class:`oem.codebook.Codebook`, the variable
matrix that Module 5 reads, the construct list that Module 3 uses, and a
diagram. Nothing here imports Streamlit.
"""

from __future__ import annotations

import copy
import re
from typing import Any

from oem import codebook, naming
from oem.library import Library

PLAN_VERSION = 2
MEASURE_KINDS = {
    "instrument": "Library instrument",
    "question": "Researcher-written question",
    "code": "Code in a coding scheme",
}
FRAMEWORK_KINDS = {
    "theory": "Theories",
    "lens": "Theoretical lenses and perspectives",
    "own": "Your own framework",
    "exploratory": "No framework in advance",
}
OWN_PREFIX = "own"
MANIFEST_FIELDS = ("Variable_ID", "Variable_Label", "Framework_Source", "Concept_Construct", "Measure", "Items")


# --------------------------------------------------------------------- plans
def empty_plan() -> dict:
    return {
        "schema_version": PLAN_VERSION,
        "frameworks": [],
        "framework_description": "",
        "concepts": [],
        "measures": [],
        "relationships": [],
        "standard_variables": [],
        "timepoints": [],
        "behavior": "",
        "narrative": "",
    }


def normalize(plan: dict | None, lib: Library | None = None) -> dict:
    """Return a version-2 plan, migrating a version-1 plan if needed."""
    if not plan:
        return empty_plan()
    if plan.get("schema_version", 1) < PLAN_VERSION:
        return migrate_v1(plan, lib or Library.load())
    out = empty_plan()
    out.update(copy.deepcopy({k: v for k, v in plan.items() if k in out}))
    return out


def concept_id(framework_id: str | None, label_or_id: str) -> str:
    """Plan-wide concept id: '<framework>.<concept>' or 'own.<slug>'."""
    local = re.sub(r"[^a-z0-9]+", "_", str(label_or_id).lower()).strip("_") or "concept"
    return f"{framework_id or OWN_PREFIX}.{local}"


def framework_concepts(lib: Library, framework_ids: list[str]) -> list[dict]:
    """Concepts supplied by the chosen frameworks, in framework order."""
    concepts = []
    for fid in framework_ids:
        for c in lib.frameworks.get(fid, {}).get("concepts", []):
            concepts.append({
                "id": concept_id(fid, c["id"]),
                "label": c["label"],
                "framework_id": fid,
                "construct_id": c.get("construct_id"),
                "definition": c.get("definition", ""),
            })
    return concepts


def default_relationships(lib: Library, framework_ids: list[str], included: set[str]) -> list[dict]:
    """The frameworks' expected paths between the concepts that were kept."""
    rows = []
    for fid in framework_ids:
        for path in lib.frameworks.get(fid, {}).get("paths", []):
            a, b = concept_id(fid, path["from"]), concept_id(fid, path["to"])
            if a in included and b in included:
                rows.append({"from": a, "to": b, "relationship": path["relationship"], "hypothesis": ""})
    return rows


def suggest_measures(lib: Library, concepts: list[dict]) -> list[dict]:
    """Library instruments (or subscales) that measure each concept's construct."""
    rows = []
    for c in concepts:
        cid = c.get("construct_id")
        if not cid:
            continue
        for inst in lib.instruments_for_constructs([cid]):
            version_id = (inst.get("versions") or [{}])[0].get("version_id")
            dims = [d for d in inst.get("dimensions", []) if cid in d.get("construct_ids", [])]
            if dims:
                for d in dims:
                    rows.append(_instrument_row(c["id"], inst["id"], version_id, d["dimension_id"]))
            elif cid in inst.get("construct_ids", []):
                rows.append(_instrument_row(c["id"], inst["id"], version_id, None))
    return rows


def _instrument_row(concept: str, instrument_id: str, version_id: str | None, dimension_id: str | None) -> dict:
    return {"concept_id": concept, "kind": "instrument", "instrument_id": instrument_id, "version_id": version_id,
            "dimension_id": dimension_id, "name": "", "label": "", "text": "", "scale_id": None}


def example_items(lib: Library, framework_id: str, behavior: str, concept_ids: set[str]) -> list[dict]:
    """App-generated draft items for a framework that offers them (currently TPB)."""
    framework = lib.frameworks.get(framework_id, {})
    examples = framework.get("example_items")
    if not examples or not behavior.strip():
        return []
    rows = []
    for local_id, templates in examples["items"].items():
        cid = concept_id(framework_id, local_id)
        if cid not in concept_ids:
            continue
        for template in templates:
            rows.append({"concept_id": cid, "kind": "question", "instrument_id": None, "version_id": None,
                         "dimension_id": None, "name": "", "label": "",
                         "text": template.format(behavior=behavior.strip()),
                         "scale_id": examples["scale_id"] if local_id != "behavior" else "frequency5"})
    return rows


# ------------------------------------------------------------------ checking
def problems(lib: Library, plan: dict) -> list[str]:
    """Things to fix before the plan's codebook can be built."""
    issues = []
    concept_ids = {c["id"] for c in plan["concepts"]}
    for fid in plan["frameworks"]:
        if fid not in lib.frameworks:
            issues.append(f"Unknown framework {fid!r}.")
    for c in plan["concepts"]:
        if c.get("construct_id") and c["construct_id"] not in lib.constructs:
            issues.append(f"Concept {c['label']!r}: unknown construct {c['construct_id']!r}.")
    for i, m in enumerate(plan["measures"], start=1):
        where = f"Measure {i}"
        if m.get("concept_id") not in concept_ids:
            issues.append(f"{where}: choose one of the plan's concepts.")
        if m.get("kind") not in MEASURE_KINDS:
            issues.append(f"{where}: choose a measure type.")
        elif m["kind"] == "instrument":
            if m.get("instrument_id") not in lib.instruments:
                issues.append(f"{where}: choose a library instrument.")
        elif not (m.get("text") or m.get("label") or "").strip():
            issues.append(f"{where}: write the question or the code's label.")
        if (m.get("name") or "").strip():
            for problem in naming.problems(m["name"].strip()):
                issues.append(f"{where}: variable name {m['name']!r} {problem}.")
        if m.get("scale_id") and m["scale_id"] not in lib.scales:
            issues.append(f"{where}: unknown response scale {m['scale_id']!r}.")
    for r in plan["relationships"]:
        if r.get("from") not in concept_ids or r.get("to") not in concept_ids:
            issues.append(f"Relationship {r.get('from')} -> {r.get('to')}: both ends must be concepts in the plan.")
    for name in plan["standard_variables"]:
        if name not in lib.standard_variables:
            issues.append(f"Unknown standard variable {name!r}.")
    for tp in plan["timepoints"]:
        if tp not in naming.TIMEPOINT_SUFFIXES:
            issues.append(f"Unknown timepoint {tp!r}.")
    if not issues:
        try:
            build_codebook(lib, plan)
        except (naming.NamingError, KeyError, ValueError) as error:
            issues.append(str(error))
    return issues


# ----------------------------------------------------------------- codebook
def _concepts(plan: dict) -> dict[str, dict]:
    return {c["id"]: c for c in plan["concepts"]}


def _score_name(prefix: str, dimension_id: str | None) -> str:
    if not dimension_id:
        return naming.check(f"{prefix}_score")
    room = naming.MAX_LENGTH - len(prefix) - 1
    return naming.check(f"{prefix}_{naming.slugify(dimension_id, room)}")


def measure_groups(lib: Library, plan: dict) -> list[dict]:
    """One group per (concept, measure): the variables that measure it, before timepoints."""
    concepts = _concepts(plan)
    counters: dict[str, int] = {}
    groups = []
    for m in plan["measures"]:
        concept = concepts.get(m.get("concept_id"))
        if not concept or m.get("kind") not in MEASURE_KINDS:
            continue
        construct_ids = [concept["construct_id"]] if concept.get("construct_id") else []
        notes = f"Measures concept: {concept['label']}"
        variables: list[codebook.Variable] = []
        if m["kind"] == "instrument":
            inst = lib.instruments.get(m.get("instrument_id"))
            if not inst:
                continue
            version_id = m.get("version_id") or (inst.get("versions") or [{}])[0].get("version_id")
            dim = next((d for d in inst.get("dimensions", []) if d["dimension_id"] == m.get("dimension_id")), None)
            title = inst["name"] + (f": {dim['name']}" if dim else "")
            if lib.items(inst["id"], version_id) and not dim:
                variables = codebook.instrument_items(lib, inst["id"], version_id)
                for v in variables:
                    v.construct_ids = sorted(set(v.construct_ids) | set(construct_ids))
                    v.notes = notes
            else:
                name = (m.get("name") or "").strip() or _score_name(inst["variable_prefix"], m.get("dimension_id"))
                variables = [codebook.Variable(
                    name=name, label=f"{title} (scale score)", data_type="numeric",
                    instrument_id=inst["id"], version_id=version_id,
                    construct_ids=sorted(set(construct_ids) | set((dim or inst).get("construct_ids", []))),
                    notes=notes + "; scale score (item-level variables are not in the library for this instrument)")]
            group_label = title
        elif m["kind"] == "question":
            counters[concept["id"]] = counters.get(concept["id"], 0) + 1
            name = (m.get("name") or "").strip() or naming.custom_variable(concept["label"], counters[concept["id"]])
            scale = lib.scales.get(m.get("scale_id") or "")
            variables = [codebook.Variable(
                name=name, label=(m.get("label") or "").strip() or f"{concept['label']} item {counters[concept['id']]}",
                data_type=("ordinal" if scale.level == "ordinal" else "categorical") if scale else "numeric",
                values=list(scale.points) if scale else [], missing=list(scale.missing) if scale else [],
                scale_id=scale.id if scale else None, question=(m.get("text") or "").strip() or None,
                construct_ids=construct_ids, notes=notes)]
            group_label = f"{concept['label']} (researcher-written items)"
        else:  # code
            label = (m.get("label") or m.get("text") or "").strip()
            name = (m.get("name") or "").strip() or naming.check("code_" + naming.slugify(label, naming.MAX_LENGTH - 5))
            selected = lib.scales.get("selected")
            variables = [codebook.Variable(
                name=name, label=f"Code: {label}", data_type="binary",
                values=list(selected.points) if selected else [(0, "Absent"), (1, "Present")],
                missing=list(selected.missing) if selected else [],
                scale_id="selected" if selected else None,
                question=(m.get("text") or "").strip() or None, construct_ids=construct_ids,
                notes=notes + "; code in a coding scheme (1 = present in the unit of analysis)")]
            group_label = f"{concept['label']} (codes)"
        groups.append({"concept": concept, "measure": m, "label": group_label, "variables": variables})
    return groups


def build_codebook(lib: Library, plan: dict) -> codebook.Codebook:
    """The plan's codebook: standard variables, then every measure, repeated per timepoint."""
    variables: list[codebook.Variable] = []
    for name in plan["standard_variables"]:
        variables += codebook.standard_variable(lib, name)
    timepoints = plan["timepoints"] or [None]
    for group in measure_groups(lib, plan):
        for tp in timepoints:
            for v in group["variables"]:
                copy_v = copy.deepcopy(v)
                copy_v.name = naming.with_timepoint(v.name, tp)
                copy_v.timepoint = tp
                variables.append(copy_v)
    names = naming.deduplicate([v.name for v in variables])
    for v, name in zip(variables, names):
        v.name = name
    return codebook.Codebook(variables)


def manifest(lib: Library, plan: dict) -> list[dict]:
    """The variable matrix Module 5 reads: one row per concept, listing its variables."""
    frameworks = {fid: lib.frameworks.get(fid, {}).get("label", fid) for fid in plan["frameworks"]}
    by_concept: dict[str, dict] = {}
    for group in measure_groups(lib, plan):
        c = group["concept"]
        row = by_concept.setdefault(c["id"], {
            "Variable_ID": naming.slugify(c["label"], 24),
            "Variable_Label": c["label"],
            "Framework_Source": frameworks.get(c.get("framework_id"), "Researcher-defined"),
            "Concept_Construct": c.get("construct_id") or c["label"],
            "Measure": [],
            "Items": [],
        })
        row["Measure"].append(group["label"])
        row["Items"] += [v.name for v in group["variables"]]
    rows = []
    for row in by_concept.values():
        rows.append({**row, "Measure": "; ".join(dict.fromkeys(row["Measure"])), "Items": "; ".join(row["Items"])})
    return rows


def construct_ids(plan: dict) -> list[str]:
    """Constructs the plan measures (for Module 3), in plan order."""
    measured = {m.get("concept_id") for m in plan["measures"]}
    return list(dict.fromkeys(c["construct_id"] for c in plan["concepts"]
                              if c.get("construct_id") and c["id"] in measured))


def profile_constructs(plan: dict) -> list[dict]:
    """Constructs for the study profile (Module 3), with the library instrument used when there is one."""
    concepts = _concepts(plan)
    out: dict[str, dict] = {}
    for m in plan["measures"]:
        concept = concepts.get(m.get("concept_id"))
        if not concept or not concept.get("construct_id"):
            continue
        cid = concept["construct_id"]
        entry = out.setdefault(cid, {"construct_id": cid, "instrument_id": None, "version_id": None, "dimension_id": None})
        if m.get("kind") == "instrument" and not entry["instrument_id"]:
            entry.update({"instrument_id": m.get("instrument_id"), "version_id": m.get("version_id"),
                          "dimension_id": m.get("dimension_id")})
    return list(out.values())


# ------------------------------------------------------------------ diagram
def _dot_text(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace('"', '\\"')


def diagram_dot(lib: Library, plan: dict) -> str:
    """Graphviz DOT source: concepts grouped by framework, with relationships."""
    counts: dict[str, int] = {}
    for m in plan["measures"]:
        counts[m.get("concept_id")] = counts.get(m.get("concept_id"), 0) + 1
    lines = ["digraph plan {", '  rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#f4f6fb", fontname="Helvetica"];',
             '  edge [fontname="Helvetica", fontsize=10];']
    groups: dict[str, list[dict]] = {}
    for c in plan["concepts"]:
        groups.setdefault(c.get("framework_id") or OWN_PREFIX, []).append(c)
    for i, (fid, concepts) in enumerate(groups.items()):
        title = lib.frameworks.get(fid, {}).get("label", "Researcher-defined concepts")
        lines.append(f'  subgraph cluster_{i} {{ label="{_dot_text(title)}"; style=dashed; color="#9aa3b5";')
        for c in concepts:
            n = counts.get(c["id"], 0)
            note = f"{n} measure{'s' if n != 1 else ''}" if n else "no measure yet"
            lines.append(f'    "{_dot_text(c["id"])}" [label="{_dot_text(c["label"])}\\n({note})"];')
        lines.append("  }")
    for r in plan["relationships"]:
        lines.append(f'  "{_dot_text(r["from"])}" -> "{_dot_text(r["to"])}" [label="{_dot_text(r.get("relationship") or "")}"];')
    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------- migration
def migrate_v1(old: dict, lib: Library) -> dict:
    """Convert a plan saved by the earlier Module 2 (schema_version 1)."""
    plan = empty_plan()
    by_label = {f["label"]: fid for fid, f in lib.frameworks.items()}
    plan["frameworks"] = [by_label[t] for t in old.get("selected_theories", []) if t in by_label]
    plan["framework_description"] = str(old.get("other_theory_sources") or "")
    plan["narrative"] = str(old.get("narrative") or "")
    plan["behavior"] = str((old.get("study_context") or {}).get("target_action") or "")
    known = {c["label"].lower(): c for c in framework_concepts(lib, plan["frameworks"])}
    concepts: dict[str, dict] = {}
    for row in list(old.get("variables") or []) + list(old.get("custom_variables") or []):
        if not isinstance(row, dict):
            continue
        label = str(row.get("Concept_Construct") or row.get("Variable_Label") or "").strip()
        if not label:
            continue
        c = known.get(label.lower()) or {"id": concept_id(None, label), "label": label, "framework_id": None,
                                         "construct_id": None, "definition": ""}
        concepts.setdefault(c["id"], c)
        text = str(row.get("Item_Text") or row.get("Question") or "").strip()
        if text:
            plan["measures"].append({"concept_id": c["id"], "kind": "question", "instrument_id": None, "version_id": None,
                                     "dimension_id": None, "name": "", "label": "", "text": text, "scale_id": None})
    plan["concepts"] = list(concepts.values())
    plan["relationships"] = default_relationships(lib, plan["frameworks"], set(concepts))
    return plan


def summary(lib: Library, plan: dict) -> dict[str, Any]:
    """What a published study summary shares about the plan: no item text, no data."""
    frameworks = [lib.frameworks[f]["label"] for f in plan["frameworks"] if f in lib.frameworks]
    variables = []
    for row in manifest(lib, plan):
        variables.append({"Variable_ID": row["Variable_ID"], "Concept_Construct": row["Concept_Construct"],
                          "Variable_Label": row["Variable_Label"], "Framework_Source": row["Framework_Source"],
                          "Instrument_Name": row["Measure"]})
    return {"selected_theories": frameworks, "framework_ids": list(plan["frameworks"]), "variables": variables}
