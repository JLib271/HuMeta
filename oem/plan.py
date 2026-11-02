# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""The variable plan built in Module 2 (Framework and Measures).

A plan runs from theory to data, and each step builds on the one before:

1. ``frameworks``: theories, lenses, the researcher's own framework, or an
   exploratory approach (ids from ``library/frameworks.json``).
2. ``constructs``: what the framework says matters. A theory's constructs are
   copied in, and the researcher can add their own. A plan construct may link
   to the shared construct vocabulary (``library/constructs.json``) through
   ``shared_construct_id``.
3. ``measures``: how each construct is measured or coded. There are three kinds:

   * ``instrument``: a library instrument, optionally one version or subscale
   * ``question``: a researcher-written item
   * ``code``: a code in a coding scheme, for texts, images, media, or interviews

4. ``relationships``: expected links between constructs. They start from the
   framework's paths and the researcher can edit them; the diagram is drawn
   from them.

The researcher decides whether an instrument fits a construct as they define
it. :func:`candidate_measures` only lists library instruments whose recorded
construct mapping matches, together with that mapping's review status.
Mappings are provisional until the HuMeta governance committee approves them.

From a plan you can build a :class:`oem.codebook.Codebook`, the variable
matrix that Module 5 reads, the constructs that Module 3 uses, and a diagram.
Nothing here imports Streamlit.
"""

from __future__ import annotations

import copy
import re
from typing import Any

from oem import codebook, naming
from oem.library import Library

PLAN_VERSION = 3
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
MAPPING_STATUS = {
    "provisional": "Provisional (not yet reviewed by the governance committee)",
    "approved": "Approved by the governance committee",
}
OWN_PREFIX = "own"
MANIFEST_FIELDS = ("Variable_ID", "Variable_Label", "Framework_Source", "Construct", "Measure", "Items")


# --------------------------------------------------------------------- plans
def empty_plan() -> dict:
    return {
        "schema_version": PLAN_VERSION,
        "frameworks": [],
        "framework_description": "",
        "constructs": [],
        "measures": [],
        "relationships": [],
        "standard_variables": [],
        "timepoints": [],
        "narrative": "",
    }


def normalize(plan: dict | None, lib: Library | None = None) -> dict:
    """Return a current-version plan, migrating an older plan if needed."""
    if not plan:
        return empty_plan()
    version = plan.get("schema_version", 1)
    if version < 2:
        return migrate_v1(plan, lib or Library.load())
    if version == 2:
        plan = migrate_v2(plan)
    out = empty_plan()
    out.update(copy.deepcopy({k: v for k, v in plan.items() if k in out}))
    out["schema_version"] = PLAN_VERSION
    return out


def construct_key(framework_id: str | None, label_or_id: str) -> str:
    """Plan-wide construct key: '<framework>.<construct>' or 'own.<slug>'."""
    local = re.sub(r"[^a-z0-9]+", "_", str(label_or_id).lower()).strip("_") or "construct"
    return f"{framework_id or OWN_PREFIX}.{local}"


FRAMEWORK_KIND_ORDER = ("theory", "lens", "own", "exploratory")


def browse_frameworks(lib: Library, field: str | None = None, kind: str | None = None, discipline: str | None = None,
                      query: str = "") -> list[str]:
    """Framework ids matching the filters (any filter left as None or "" is ignored), theories first.

    The search matches the name, description, citation (so authors' names work), and construct names.
    'My own framework' and 'Exploratory' are kept whatever the filters, because they suit every study.
    """
    words = [w for w in re.split(r"\s+", (query or "").lower()) if w]
    out = []
    for fid, fw in lib.frameworks.items():
        always = fw["kind"] in ("own", "exploratory")
        if not always:
            if field and field not in fw.get("fields", []):
                continue
            if kind and fw["kind"] != kind:
                continue
            if discipline and discipline not in fw.get("disciplines", []):
                continue
            if words:
                text = " ".join([fw["label"], fw.get("description", ""), fw.get("citation", "")]
                                + [c["label"] for c in fw.get("constructs", [])]).lower()
                if not all(w in text for w in words):
                    continue
        out.append(fid)
    return sorted(out, key=lambda fid: (FRAMEWORK_KIND_ORDER.index(lib.frameworks[fid]["kind"]),
                                        lib.frameworks[fid]["label"].lower()))


def framework_constructs(lib: Library, framework_ids: list[str]) -> list[dict]:
    """Constructs supplied by the chosen frameworks, in framework order."""
    constructs = []
    for fid in framework_ids:
        for c in lib.frameworks.get(fid, {}).get("constructs", []):
            constructs.append({
                "id": construct_key(fid, c["id"]),
                "label": c["label"],
                "framework_id": fid,
                "shared_construct_id": c.get("shared_construct_id"),
                "definition": c.get("definition", ""),
            })
    return constructs


def default_relationships(lib: Library, framework_ids: list[str], included: set[str]) -> list[dict]:
    """The frameworks' expected paths between the constructs that were kept."""
    rows = []
    for fid in framework_ids:
        for path in lib.frameworks.get(fid, {}).get("paths", []):
            a, b = construct_key(fid, path["from"]), construct_key(fid, path["to"])
            if a in included and b in included:
                rows.append({"from": a, "to": b, "relationship": path["relationship"], "hypothesis": ""})
    return rows


def mapping_status(instrument: dict) -> str:
    """Review status of an instrument's construct mapping (provisional unless approved)."""
    return (instrument.get("construct_mapping") or {}).get("status", "provisional")


def candidate_measures(lib: Library, constructs: list[dict]) -> list[dict]:
    """Library instruments (or subscales) recorded as measuring each construct's shared construct.

    These are candidates for the researcher to judge, not recommendations: each
    row carries the mapping's review status and what the instrument part was
    developed to measure.
    """
    rows = []
    for c in constructs:
        cid = c.get("shared_construct_id")
        if not cid:
            continue
        for inst in lib.instruments_for_constructs([cid]):
            version_id = (inst.get("versions") or [{}])[0].get("version_id")
            dims = [d for d in inst.get("dimensions", []) if cid in d.get("construct_ids", [])]
            parts = [(d["dimension_id"], d["name"], d.get("construct_ids", [])) for d in dims]
            if not parts and cid in inst.get("construct_ids", []):
                parts = [(None, "Whole instrument", inst.get("construct_ids", []))]
            for dimension_id, part, measured in parts:
                rows.append({
                    "construct": c["id"], "kind": "instrument", "instrument_id": inst["id"], "version_id": version_id,
                    "dimension_id": dimension_id, "name": "", "label": "", "text": "", "scale_id": None,
                    "part": part,
                    "measures": [lib.constructs[m]["label"] for m in measured if m in lib.constructs],
                    "mapping_status": mapping_status(inst),
                })
    return rows


MEASURE_KEYS = ("construct", "kind", "instrument_id", "version_id", "dimension_id", "name", "label", "text", "scale_id")


def as_measure(row: dict) -> dict:
    """Keep only the fields a plan measure stores (drops candidate display fields)."""
    return {k: row.get(k) for k in MEASURE_KEYS}


# ------------------------------------------------------------------ checking
def problems(lib: Library, plan: dict) -> list[str]:
    """Things to fix before the plan's codebook can be built."""
    issues = []
    keys = {c["id"] for c in plan["constructs"]}
    for fid in plan["frameworks"]:
        if fid not in lib.frameworks:
            issues.append(f"Unknown framework {fid!r}.")
    for c in plan["constructs"]:
        if c.get("shared_construct_id") and c["shared_construct_id"] not in lib.constructs:
            issues.append(f"Construct {c['label']!r}: unknown shared construct {c['shared_construct_id']!r}.")
    for i, m in enumerate(plan["measures"], start=1):
        where = f"Measure {i}"
        if m.get("construct") not in keys:
            issues.append(f"{where}: choose one of the plan's constructs.")
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
        if r.get("from") not in keys or r.get("to") not in keys:
            issues.append(f"Relationship {r.get('from')} -> {r.get('to')}: both ends must be constructs in the plan.")
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
def _constructs(plan: dict) -> dict[str, dict]:
    return {c["id"]: c for c in plan["constructs"]}


def _score_name(prefix: str, dimension_id: str | None) -> str:
    if not dimension_id:
        return naming.check(f"{prefix}_score")
    room = naming.MAX_LENGTH - len(prefix) - 1
    return naming.check(f"{prefix}_{naming.slugify(dimension_id, room)}")


def measure_groups(lib: Library, plan: dict) -> list[dict]:
    """One group per (construct, measure): the variables that measure it, before timepoints."""
    constructs = _constructs(plan)
    counters: dict[str, int] = {}
    groups = []
    for m in plan["measures"]:
        construct = constructs.get(m.get("construct"))
        if not construct or m.get("kind") not in MEASURE_KINDS:
            continue
        shared = [construct["shared_construct_id"]] if construct.get("shared_construct_id") else []
        notes = f"Measures construct: {construct['label']}"
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
                    v.construct_ids = sorted(set(v.construct_ids) | set(shared))
                    v.notes = notes
            else:
                name = (m.get("name") or "").strip() or _score_name(inst["variable_prefix"], m.get("dimension_id"))
                variables = [codebook.Variable(
                    name=name, label=f"{title} (scale score)", data_type="numeric",
                    instrument_id=inst["id"], version_id=version_id,
                    construct_ids=sorted(set(shared) | set((dim or inst).get("construct_ids", []))),
                    notes=notes + "; scale score (item-level variables are not in the library for this instrument)")]
            group_label = title
        elif m["kind"] == "question":
            counters[construct["id"]] = counters.get(construct["id"], 0) + 1
            name = (m.get("name") or "").strip() or naming.custom_variable(construct["label"], counters[construct["id"]])
            scale = lib.scales.get(m.get("scale_id") or "")
            variables = [codebook.Variable(
                name=name, label=(m.get("label") or "").strip() or f"{construct['label']} item {counters[construct['id']]}",
                data_type=("ordinal" if scale.level == "ordinal" else "categorical") if scale else "numeric",
                values=list(scale.points) if scale else [], missing=list(scale.missing) if scale else [],
                scale_id=scale.id if scale else None, question=(m.get("text") or "").strip() or None,
                construct_ids=shared, notes=notes)]
            group_label = f"{construct['label']} (researcher-written items)"
        else:  # code
            label = (m.get("label") or m.get("text") or "").strip()
            name = (m.get("name") or "").strip() or naming.check("code_" + naming.slugify(label, naming.MAX_LENGTH - 5))
            selected = lib.scales.get("selected")
            variables = [codebook.Variable(
                name=name, label=f"Code: {label}", data_type="binary",
                values=list(selected.points) if selected else [(0, "Absent"), (1, "Present")],
                missing=list(selected.missing) if selected else [],
                scale_id="selected" if selected else None,
                question=(m.get("text") or "").strip() or None, construct_ids=shared,
                notes=notes + "; code in a coding scheme (1 = present in the unit of analysis)")]
            group_label = f"{construct['label']} (codes)"
        groups.append({"construct": construct, "measure": m, "label": group_label, "variables": variables})
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


def alignment(lib: Library, plan: dict) -> list[dict]:
    """Construct -> measure -> variables, one row per measure, for review in Module 2."""
    rows = []
    for group in measure_groups(lib, plan):
        m, c = group["measure"], group["construct"]
        inst = lib.instruments.get(m.get("instrument_id") or "")
        rows.append({
            "Construct": c["label"],
            "Shared construct": lib.constructs.get(c.get("shared_construct_id") or "", {}).get("label", ""),
            "Measure": group["label"],
            "Variables": ", ".join(v.name for v in group["variables"]),
            "Mapping status": MAPPING_STATUS[mapping_status(inst)] if inst else "Researcher-defined",
        })
    return rows


def manifest(lib: Library, plan: dict) -> list[dict]:
    """The variable matrix Module 5 reads: one row per construct, listing its variables."""
    frameworks = {fid: lib.frameworks.get(fid, {}).get("label", fid) for fid in plan["frameworks"]}
    by_construct: dict[str, dict] = {}
    for group in measure_groups(lib, plan):
        c = group["construct"]
        row = by_construct.setdefault(c["id"], {
            "Variable_ID": naming.slugify(c["label"], 24),
            "Variable_Label": c["label"],
            "Framework_Source": frameworks.get(c.get("framework_id"), "Researcher-defined"),
            "Construct": c.get("shared_construct_id") or c["label"],
            "Measure": [],
            "Items": [],
        })
        row["Measure"].append(group["label"])
        row["Items"] += [v.name for v in group["variables"]]
    return [{**row, "Measure": "; ".join(dict.fromkeys(row["Measure"])), "Items": "; ".join(row["Items"])}
            for row in by_construct.values()]


def shared_construct_ids(plan: dict) -> list[str]:
    """Shared constructs the plan measures (for Module 3), in plan order."""
    measured = {m.get("construct") for m in plan["measures"]}
    return list(dict.fromkeys(c["shared_construct_id"] for c in plan["constructs"]
                              if c.get("shared_construct_id") and c["id"] in measured))


def profile_constructs(plan: dict) -> list[dict]:
    """Constructs for the study profile (Module 3), with the library instrument used when there is one."""
    constructs = _constructs(plan)
    out: dict[str, dict] = {}
    for m in plan["measures"]:
        construct = constructs.get(m.get("construct"))
        if not construct or not construct.get("shared_construct_id"):
            continue
        cid = construct["shared_construct_id"]
        entry = out.setdefault(cid, {"construct_id": cid, "instrument_id": None, "version_id": None, "dimension_id": None})
        if m.get("kind") == "instrument" and not entry["instrument_id"]:
            entry.update({"instrument_id": m.get("instrument_id"), "version_id": m.get("version_id"),
                          "dimension_id": m.get("dimension_id")})
    return list(out.values())


# ------------------------------------------------------------------ diagram
def _dot_text(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace('"', '\\"')


def diagram_dot(lib: Library, plan: dict) -> str:
    """Graphviz DOT source: constructs grouped by framework, with relationships."""
    counts: dict[str, int] = {}
    for m in plan["measures"]:
        counts[m.get("construct")] = counts.get(m.get("construct"), 0) + 1
    lines = ["digraph plan {", '  rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#f4f6fb", fontname="Helvetica"];',
             '  edge [fontname="Helvetica", fontsize=10];']
    groups: dict[str, list[dict]] = {}
    for c in plan["constructs"]:
        groups.setdefault(c.get("framework_id") or OWN_PREFIX, []).append(c)
    for i, (fid, constructs) in enumerate(groups.items()):
        title = lib.frameworks.get(fid, {}).get("label", "Researcher-defined constructs")
        lines.append(f'  subgraph cluster_{i} {{ label="{_dot_text(title)}"; style=dashed; color="#9aa3b5";')
        for c in constructs:
            n = counts.get(c["id"], 0)
            note = f"{n} measure{'s' if n != 1 else ''}" if n else "no measure yet"
            lines.append(f'    "{_dot_text(c["id"])}" [label="{_dot_text(c["label"])}\\n({note})"];')
        lines.append("  }")
    for r in plan["relationships"]:
        lines.append(f'  "{_dot_text(r["from"])}" -> "{_dot_text(r["to"])}" [label="{_dot_text(r.get("relationship") or "")}"];')
    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------- migration
def migrate_v2(old: dict) -> dict:
    """Version 2 called constructs 'concepts'; rename the keys."""
    plan = copy.deepcopy(old)
    plan["constructs"] = [
        {"id": c["id"], "label": c["label"], "framework_id": c.get("framework_id"),
         "shared_construct_id": c.get("construct_id"), "definition": c.get("definition", "")}
        for c in plan.pop("concepts", [])]
    for m in plan.get("measures", []):
        m["construct"] = m.pop("concept_id", m.get("construct"))
    plan.pop("behavior", None)
    plan["schema_version"] = PLAN_VERSION
    return plan


def migrate_v1(old: dict, lib: Library) -> dict:
    """Convert a plan saved by the earliest Module 2 (schema_version 1)."""
    plan = empty_plan()
    by_label = {f["label"]: fid for fid, f in lib.frameworks.items()}
    plan["frameworks"] = [by_label[t] for t in old.get("selected_theories", []) if t in by_label]
    plan["framework_description"] = str(old.get("other_theory_sources") or "")
    plan["narrative"] = str(old.get("narrative") or "")
    known = {c["label"].lower(): c for c in framework_constructs(lib, plan["frameworks"])}
    constructs: dict[str, dict] = {}
    for row in list(old.get("variables") or []) + list(old.get("custom_variables") or []):
        if not isinstance(row, dict):
            continue
        label = str(row.get("Concept_Construct") or row.get("Variable_Label") or "").strip()
        if not label:
            continue
        c = known.get(label.lower()) or {"id": construct_key(None, label), "label": label, "framework_id": None,
                                         "shared_construct_id": None, "definition": ""}
        constructs.setdefault(c["id"], c)
        text = str(row.get("Item_Text") or row.get("Question") or "").strip()
        if text:
            plan["measures"].append({**{k: None for k in MEASURE_KEYS}, "construct": c["id"], "kind": "question",
                                     "name": "", "label": "", "text": text})
    plan["constructs"] = list(constructs.values())
    plan["relationships"] = default_relationships(lib, plan["frameworks"], set(constructs))
    return plan


def summary(lib: Library, plan: dict) -> dict[str, Any]:
    """What a published study summary shares about the plan: no item text, no data."""
    frameworks = [lib.frameworks[f]["label"] for f in plan["frameworks"] if f in lib.frameworks]
    variables = [{"Variable_ID": row["Variable_ID"], "Construct": row["Construct"], "Variable_Label": row["Variable_Label"],
                  "Framework_Source": row["Framework_Source"], "Instrument_Name": row["Measure"]}
                 for row in manifest(lib, plan)]
    return {"selected_theories": frameworks, "framework_ids": list(plan["frameworks"]), "variables": variables}
