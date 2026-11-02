# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 2: Framework and Measures.

Theory organizes the module. Choose a framework (a theory, a lens, your own
framework, or an exploratory approach); the framework supplies concepts; each
concept gets measures (library instruments, researcher-written questions, or
codes in a coding scheme); expected relationships come from the framework and
draw the diagram. The result is the variable plan and its codebook. The plan
logic lives in ``oem/plan.py``.
"""

from __future__ import annotations

import json
import time

import pandas as pd
import streamlit as st

from oem import plan as P
from oem.app.common import (APP_DIR, automate_github_pull_request, context_search_terms, current_project,
                            load_published_summaries, open_review_pull_request, public_submission_warning,
                            render_project_download, safe_slug)
from oem.app.profile_form import current_record, library, store_record

KIND_ORDER = ["theory", "lens", "own", "exploratory"]
KIND_PREFIX = {"theory": "Theory", "lens": "Lens", "own": "Own", "exploratory": "Exploratory"}


# ----------------------------------------------------------- working state
def _project_plan_marker(project: dict) -> str:
    return json.dumps(project.get("module2_plan") or {}, sort_keys=True, default=str)


def _base(lib) -> dict:
    """The plan snapshot that widget defaults come from (refreshed when the project changes)."""
    project = current_project()
    marker = _project_plan_marker(project)
    if st.session_state.get("m2_marker") != marker or "m2_base" not in st.session_state:
        base = P.normalize(project.get("module2_plan"), lib)
        record = current_record()
        if not base["frameworks"] and record:
            design = record["study"]["design"]
            base["frameworks"] = [f for f in design.get("frameworks") or [] if f in lib.frameworks]
            base["framework_description"] = base["framework_description"] or (design.get("framework_description") or "")
        if base["frameworks"] and not base["concepts"]:
            base["concepts"] = P.framework_concepts(lib, base["frameworks"])
        if not base["relationships"]:
            base["relationships"] = P.default_relationships(lib, base["frameworks"], {c["id"] for c in base["concepts"]})
        st.session_state["m2_base"] = base
        st.session_state["m2_marker"] = marker
        st.session_state["m2_version"] = st.session_state.get("m2_version", 0) + 1
        st.session_state.pop("m2_pending", None)
    elif f"m2_frameworks_{st.session_state['m2_version']}" not in st.session_state and st.session_state.get("m2_pending"):
        # Returning from another page: Streamlit dropped the widgets, so restore unsaved edits.
        st.session_state["m2_base"] = st.session_state["m2_pending"]
        st.session_state["m2_version"] += 1
    return st.session_state["m2_base"]


def _rebase(plan: dict) -> None:
    """Make ``plan`` the new widget baseline (after a button changes it) and refresh the widgets."""
    st.session_state["m2_base"] = plan
    st.session_state["m2_pending"] = plan
    st.session_state["m2_version"] = st.session_state.get("m2_version", 0) + 1
    st.rerun()


def _s(value) -> str:
    """Cell text from a data editor ('' for empty cells, which pandas returns as None or NaN)."""
    if value is None or (isinstance(value, float) and value != value):
        return ""
    return str(value).strip()


def _concept_label(lib, concept: dict) -> str:
    fid = concept.get("framework_id")
    source = lib.frameworks[fid]["label"].split(" (")[0] if fid in lib.frameworks else "your concept"
    return f"{concept['label']} — {source}"


def _instrument_options(lib) -> dict[str, tuple[str, str | None, str | None]]:
    options = {}
    for iid, inst in sorted(lib.instruments.items(), key=lambda kv: kv[1]["name"]):
        version_id = (inst.get("versions") or [{}])[0].get("version_id")
        short = inst.get("acronym") or inst["name"]
        options[f"{short} (whole instrument)"] = (iid, version_id, None)
        for d in inst.get("dimensions", []):
            options[f"{short}: {d['name']}"] = (iid, version_id, d["dimension_id"])
    return options


def _instrument_label(options: dict, m: dict) -> str | None:
    for label, (iid, _, did) in options.items():
        if iid == m.get("instrument_id") and did == m.get("dimension_id"):
            return label
    return None


# ------------------------------------------------------------------ page
def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    lib = library()
    base = _base(lib)
    v = st.session_state["m2_version"]

    st.header("2. Framework and Measures")
    st.caption(
        "Start from theory. Choose the framework that guides your study, and it supplies the concepts. Give each "
        "concept a measure (a library instrument, your own questions, or codes in a coding scheme), and the "
        "framework's expected relationships draw the diagram. The result is your variable plan and its codebook."
    )
    if current_record() is None:
        st.info("Tip: save your study profile in Module 1 first, so this module can use your topic and framework.")

    plan = P.empty_plan()
    plan["timepoints"], plan["standard_variables"] = list(base["timepoints"]), list(base["standard_variables"])

    # ------------------------------------------------------------ Step 1
    st.subheader("Step 1 · Framework")
    kinds = {fid: f["kind"] for fid, f in lib.frameworks.items()}
    options = sorted(lib.frameworks, key=lambda fid: (KIND_ORDER.index(kinds[fid]), lib.frameworks[fid]["label"]))
    plan["frameworks"] = st.multiselect(
        "Theory, lens, or approach that guides your study *", options,
        default=[f for f in base["frameworks"] if f in lib.frameworks],
        format_func=lambda fid: f"{KIND_PREFIX[kinds[fid]]}: {lib.frameworks[fid]['label']}",
        key=f"m2_frameworks_{v}",
        help="Choose one or more. Pick 'My own conceptual framework' to define your own concepts, or "
             "'Exploratory or inductive' if concepts will emerge from the data.",
    )
    for fid in plan["frameworks"]:
        f = lib.frameworks[fid]
        cite = f.get("citation") or "Cite the specific work you draw on."
        if f.get("doi"):
            cite += f" https://doi.org/{f['doi']}"
        st.caption(f"**{f['label']}.** {f['description']} *{cite}*")
    plan["framework_description"] = st.text_area(
        "How does the framework guide your study?" + (" *" if {"own", "lens"} & {kinds[f] for f in plan["frameworks"]} else ""),
        base["framework_description"], key=f"m2_fdesc_{v}",
        help="Required for your own framework or a lens: describe it and the ideas it brings.")
    if not plan["frameworks"]:
        st.warning("Choose a framework, or 'Exploratory or inductive' if you are not starting from one.")
    related = _related_studies(lib, plan["frameworks"])
    if related:
        with st.expander(f"Published studies using the same framework ({len(related)})"):
            for item in related:
                st.markdown(f"- **{item.get('study_title', 'Untitled')}**: "
                            + ", ".join((item.get("study_metadata") or {}).get("selected_theories", [])))

    # ------------------------------------------------------------ Step 2
    st.subheader("Step 2 · Concepts")
    st.caption("The framework supplies its concepts. Keep the ones your study addresses and add your own.")
    base_by_framework: dict[str, list[str]] = {}
    for c in base["concepts"]:
        base_by_framework.setdefault(c.get("framework_id") or "", []).append(c["id"])
    concepts: list[dict] = []
    for fid in plan["frameworks"]:
        available = P.framework_concepts(lib, [fid])
        if not available:
            continue
        labels = {c["id"]: c for c in available}
        default = [cid for cid in base_by_framework.get(fid, list(labels)) if cid in labels] if fid in base["frameworks"] else list(labels)
        chosen = st.multiselect(f"Concepts from {lib.frameworks[fid]['label']}", list(labels), default=default,
                                format_func=lambda cid, labels=labels: labels[cid]["label"] + (
                                    f"  ·  construct: {lib.constructs[labels[cid]['construct_id']]['label']}"
                                    if labels[cid].get("construct_id") in lib.constructs else ""),
                                key=f"m2_fc_{fid}_{v}")
        concepts += [labels[cid] for cid in chosen]
    construct_labels = {c["label"]: cid for cid, c in sorted(lib.constructs.items(), key=lambda kv: kv[1]["label"])}
    construct_names = {cid: label for label, cid in construct_labels.items()}
    own_base = [c for c in base["concepts"] if not c.get("framework_id")]
    own_df = st.data_editor(
        pd.DataFrame([{"Concept": c["label"], "Definition": c.get("definition", ""),
                       "Construct (optional)": construct_names.get(c.get("construct_id"))} for c in own_base],
                     columns=["Concept", "Definition", "Construct (optional)"]),
        num_rows="dynamic", use_container_width=True, key=f"m2_own_{v}",
        column_config={"Construct (optional)": st.column_config.SelectboxColumn(
            "Construct (optional)", options=list(construct_labels),
            help="Link to the shared construct list so Module 3 and searches can use it.")},
    )
    st.caption("Your own concepts: for your own framework, a lens's ideas, or concepts emerging from exploratory work.")
    seen = {c["id"] for c in concepts}
    for row in own_df.to_dict(orient="records"):
        label = _s(row.get("Concept"))
        if not label:
            continue
        cid = P.concept_id(None, label)
        if cid in seen:
            continue
        seen.add(cid)
        concepts.append({"id": cid, "label": label, "framework_id": None,
                         "construct_id": construct_labels.get(_s(row.get("Construct (optional)"))),
                         "definition": _s(row.get("Definition"))})
    plan["concepts"] = concepts
    concept_ids = {c["id"] for c in concepts}
    concept_display = {_concept_label(lib, c): c["id"] for c in concepts}
    concept_from_id = {cid: label for label, cid in concept_display.items()}

    # ------------------------------------------------------------ Step 3
    st.subheader("Step 3 · Measures and codes")
    st.caption(
        "Give each concept at least one measure: a library instrument or subscale, your own questions, or codes in a "
        "coding scheme (for texts, images, media, or interviews). Variable names are generated from the library and "
        "the concept, so studies using the same measure share names."
    )
    instrument_options = _instrument_options(lib)
    scale_labels = {s.label: sid for sid, s in lib.scales.items()}
    scale_names = {sid: label for label, sid in scale_labels.items()}
    kind_labels = {label: kind for kind, label in P.MEASURE_KINDS.items()}
    measures_df = st.data_editor(
        pd.DataFrame([{
            "Concept": concept_from_id.get(m.get("concept_id")),
            "Type": P.MEASURE_KINDS.get(m.get("kind")),
            "Library instrument": _instrument_label(instrument_options, m) if m.get("kind") == "instrument" else None,
            "Question, or code definition": m.get("text") or "",
            "Label (code name or item label)": m.get("label") or "",
            "Response scale": scale_names.get(m.get("scale_id")),
            "Variable name (optional)": m.get("name") or "",
        } for m in base["measures"]], columns=["Concept", "Type", "Library instrument", "Question, or code definition",
                                               "Label (code name or item label)", "Response scale", "Variable name (optional)"]),
        num_rows="dynamic", use_container_width=True, key=f"m2_measures_{v}",
        column_config={
            "Concept": st.column_config.SelectboxColumn("Concept", options=list(concept_display), required=True),
            "Type": st.column_config.SelectboxColumn("Type", options=list(kind_labels), required=True),
            "Library instrument": st.column_config.SelectboxColumn("Library instrument", options=list(instrument_options)),
            "Response scale": st.column_config.SelectboxColumn("Response scale", options=list(scale_labels)),
        },
    )
    measures = []
    for row in measures_df.to_dict(orient="records"):
        if not _s(row.get("Concept")) and not _s(row.get("Type")):
            continue
        iid, vid, did = instrument_options.get(_s(row.get("Library instrument")), (None, None, None))
        measures.append({"concept_id": concept_display.get(_s(row.get("Concept"))), "kind": kind_labels.get(_s(row.get("Type"))),
                         "instrument_id": iid, "version_id": vid, "dimension_id": did,
                         "name": _s(row.get("Variable name (optional)")),
                         "label": _s(row.get("Label (code name or item label)")),
                         "text": _s(row.get("Question, or code definition")),
                         "scale_id": scale_labels.get(_s(row.get("Response scale")))})
    plan["measures"] = measures
    suggestions = [m for m in P.suggest_measures(lib, concepts)
                   if (m["concept_id"], m["instrument_id"], m["dimension_id"])
                   not in {(x["concept_id"], x["instrument_id"], x["dimension_id"]) for x in measures}]
    if st.button(f"Add {len(suggestions)} library measure(s) for my concepts", disabled=not suggestions,
                 key=f"m2_add_lib_{v}", help="Instruments and subscales in the library that measure your concepts' constructs."):
        _rebase({**plan, "measures": measures + suggestions, "relationships": base["relationships"]})
    unmeasured = [c["label"] for c in concepts if c["id"] not in {m["concept_id"] for m in measures}]
    if unmeasured:
        st.warning("No measure yet for: " + ", ".join(unmeasured))
    used = {m["instrument_id"] for m in measures if m["kind"] == "instrument" and m["instrument_id"]}
    if used:
        with st.expander("About the library instruments in your plan"):
            for iid in sorted(used):
                inst = lib.instruments[iid]
                access = inst.get("access", {})
                text_ok = "Item text is in the library" if lib.item_text_allowed(iid) and any(
                    key[0] == iid for key in lib.item_files) else "Item text is not stored here; get it from the source"
                cite = (inst.get("original_citation") or {}).get("text") or ""
                st.markdown(f"**{inst['name']}**. {text_ok}. Access: {access.get('terms_summary', access.get('access_type', ''))} {cite}")

    # ------------------------------------------------------------ Step 4
    st.subheader("Step 4 · Relationships and diagram")
    st.caption("Expected relationships start from the framework. Edit them, add your own, and note hypotheses.")
    rel_df = st.data_editor(
        pd.DataFrame([{"From": concept_from_id.get(r["from"]), "To": concept_from_id.get(r["to"]),
                       "Relationship": r.get("relationship", ""), "Hypothesis or rationale": r.get("hypothesis", "")}
                      for r in base["relationships"] if r["from"] in concept_ids and r["to"] in concept_ids],
                     columns=["From", "To", "Relationship", "Hypothesis or rationale"]),
        num_rows="dynamic", use_container_width=True, key=f"m2_rel_{v}",
        column_config={"From": st.column_config.SelectboxColumn("From", options=list(concept_display)),
                       "To": st.column_config.SelectboxColumn("To", options=list(concept_display))},
    )
    plan["relationships"] = [
        {"from": concept_display[_s(r.get("From"))], "to": concept_display[_s(r.get("To"))],
         "relationship": _s(r.get("Relationship")), "hypothesis": _s(r.get("Hypothesis or rationale"))}
        for r in rel_df.to_dict(orient="records") if _s(r.get("From")) in concept_display and _s(r.get("To")) in concept_display]
    defaults = [r for r in P.default_relationships(lib, plan["frameworks"], concept_ids)
                if (r["from"], r["to"]) not in {(x["from"], x["to"]) for x in plan["relationships"]}]
    if defaults and st.button(f"Add the framework's {len(defaults)} expected relationship(s)", key=f"m2_paths_{v}"):
        _rebase({**plan, "relationships": plan["relationships"] + defaults})
    if concepts:
        st.graphviz_chart(P.diagram_dot(lib, plan), use_container_width=True)
    plan["narrative"] = st.text_area("Conceptual framework narrative (optional)", base.get("narrative", ""),
                                     key=f"m2_narrative_{v}")

    # ------------------------------------------------------------ Step 5
    st.subheader("Step 5 · Review and save")
    c1, c2 = st.columns(2)
    std_labels = {f"{s['label']} ({name})": name for name, s in lib.standard_variables.items()}
    plan["standard_variables"] = [std_labels[x] for x in c1.multiselect(
        "Standard and demographic variables", list(std_labels),
        default=[k for k, name in std_labels.items() if name in base["standard_variables"]], key=f"m2_std_{v}",
        help="Shared definitions from the library, so these columns match across studies.")]
    plan["timepoints"] = c2.multiselect("Timepoints (for repeated measures)", list(P.naming.TIMEPOINT_SUFFIXES),
                                        default=base["timepoints"], key=f"m2_tp_{v}",
                                        help="Each measured variable is repeated with this suffix, e.g. _pre and _post.")
    issues = P.problems(lib, plan)
    if {"own", "lens"} & {kinds[f] for f in plan["frameworks"]} and not plan["framework_description"].strip():
        issues.append("Describe your own framework or lens in Step 1.")
    for issue in issues:
        st.error(issue)
    book = None
    if not issues and plan["measures"]:
        book = P.build_codebook(lib, plan)
        st.markdown(f"**Codebook:** {len(book)} variables for {len(concepts)} concepts.")
        st.dataframe(pd.DataFrame(book.to_rows())[["name", "label", "data_type", "values", "question", "construct_ids", "notes"]],
                     use_container_width=True, hide_index=True)
        manifest = P.manifest(lib, plan)
        st.session_state["module2_variable_manifest"] = manifest
        d1, d2, d3, d4 = st.columns(4)
        d1.download_button("Codebook (CSV)", book.to_csv().encode("utf-8"), file_name="codebook.csv", mime="text/csv", key="m2_dl_cb_csv")
        d2.download_button("Codebook (JSON)", book.to_json().encode("utf-8"), file_name="codebook.json", mime="application/json", key="m2_dl_cb_json")
        d3.download_button("Variable matrix for Module 5 (CSV)", pd.DataFrame(manifest).to_csv(index=False).encode("utf-8"),
                           file_name="variable_matrix.csv", mime="text/csv", key="m2_dl_manifest")
        d4.download_button("Diagram (Graphviz DOT)", P.diagram_dot(lib, plan).encode("utf-8"), file_name="framework_diagram.dot", mime="text/vnd.graphviz", key="m2_dl_dot")
    if st.button("Save variable plan to project", type="primary", disabled=bool(issues), key="m2_save"):
        project = current_project()
        project["module2_plan"] = plan
        st.session_state["project"] = project
        st.session_state["m2_marker"] = _project_plan_marker(project)
        record = current_record()
        if record is not None:
            record["study"]["design"]["frameworks"] = list(plan["frameworks"])
            if plan["framework_description"].strip():
                record["study"]["design"]["framework_description"] = plan["framework_description"].strip()
            store_record(record, reset_widgets=True)
        st.session_state["m2_saved"] = True
        _rebase(plan)
    if st.session_state.get("m2_saved"):
        st.success("Variable plan saved to your project" + (", and your study profile now lists the framework." if current_record()
                                                             else ".") + " Download the project file to keep it; the app does not store a copy.")
        render_project_download(key="m2_project_download")

    st.session_state["m2_pending"] = plan
    _share(lib, plan, book, publish_disabled, publish_hint)


def _related_studies(lib, framework_ids: list[str]) -> list[dict]:
    if not framework_ids:
        return []
    wanted_ids = set(framework_ids)
    wanted_labels = {lib.frameworks[f]["label"] for f in framework_ids if f in lib.frameworks}
    found = []
    for item in load_published_summaries():
        meta = item.get("study_metadata") or {}
        if wanted_ids & set(meta.get("framework_ids", [])) or wanted_labels & set(meta.get("selected_theories", [])):
            found.append(item)
    return found


def _share(lib, plan: dict, book, publish_disabled: bool, publish_hint: str | None) -> None:
    st.markdown("---")
    st.subheader("Share (optional)")
    project = current_project()
    study = project.get("study") or {}
    with st.expander("Publish a limited study summary for other researchers"):
        if not study or book is None:
            st.info("Save a study profile in Module 1 and complete this plan first.")
        else:
            study_id = str(study.get("id"))
            summary_path = f"published/study_summaries/{safe_slug(study_id, 'study')}.json"
            try:
                meta = json.loads(study.get("study_description") or "{}").get("metadata", {})
            except (TypeError, json.JSONDecodeError):
                meta = {}
            shared = P.summary(lib, plan)
            summary_record = {
                "schema_version": 2,
                "study_id": study_id,
                "study_title": study.get("study_title") or "Shared study",
                "context_tags": context_search_terms(" ".join([meta.get("content_domain", ""), *shared["selected_theories"],
                                                               *[c["label"] for c in plan["concepts"]]])),
                "study_metadata": {
                    "content_domain": meta.get("content_domain", ""),
                    "time_method": meta.get("time_method", ""),
                    "unit_of_analysis": meta.get("unit_of_analysis", ""),
                    "participant_populations": meta.get("participant_populations", []),
                    "study_settings": meta.get("study_settings", []),
                    **shared,
                },
                "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            st.caption("Shares the framework, concepts, and measures, with no item text, data, or participant information.")
            public_submission_warning()
            st.json(summary_record)
            consent = st.checkbox("I confirm this summary contains no participant data or confidential information, I am "
                                  "authorized to make it public, and I understand it is visible on GitHub as soon as I submit it.",
                                  key="m2_summary_consent")
            already = (APP_DIR / summary_path).is_file()
            if st.button("Update published summary" if already else "Submit summary for public listing",
                         disabled=publish_disabled or not consent, help=publish_hint, key="m2_summary_submit"):
                with st.spinner("Opening a pull request for maintainer review..."):
                    message = open_review_pull_request(
                        suggestion_type="Study Summary", title_summary=str(summary_record["study_title"])[:120],
                        files={summary_path: json.dumps(summary_record, ensure_ascii=False, indent=2)},
                        description="Adds or updates a limited study summary for discovery.")
                (st.error if "❌" in message else st.success)(message)
            if already and st.button("Request removal of the published summary", disabled=publish_disabled,
                                     help=publish_hint, key="m2_summary_remove"):
                with st.spinner("Opening a removal pull request..."):
                    message = open_review_pull_request(
                        suggestion_type="Remove Study Summary", title_summary=str(study.get("study_title") or study_id)[:120],
                        delete_paths=[summary_path], description="Removes this study summary. Earlier versions remain in git history.")
                (st.error if "❌" in message else st.success)(message)

    with st.expander("Suggest a theory or lens for the framework list"):
        st.caption("Frameworks live in `library/frameworks.json`. Suggestions are reviewed before they are added.")
        public_submission_warning()
        name = st.text_input("Theory or lens name", key="m2_fw_name")
        kind = st.selectbox("Kind", ["theory", "lens"], key="m2_fw_kind")
        concepts = st.text_area("Concepts (one per line; for a theory)", key="m2_fw_concepts")
        citation = st.text_input("Key citation (with DOI if there is one)", key="m2_fw_citation")
        rationale = st.text_area("Why add it?", key="m2_fw_rationale")
        consent = st.checkbox("I confirm this suggestion contains no confidential information and may be published.",
                              key="m2_fw_consent")
        if st.button("Submit suggestion", disabled=publish_disabled or not (consent and name.strip() and citation.strip()),
                     help=publish_hint, key="m2_fw_submit"):
            payload = json.dumps({"label": name.strip(), "kind": kind,
                                  "concepts": [c.strip() for c in concepts.splitlines() if c.strip()],
                                  "citation": citation.strip(), "rationale": rationale.strip(),
                                  "submitted_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                                 ensure_ascii=False, indent=2)
            with st.spinner("Opening a pull request for maintainer review..."):
                message = automate_github_pull_request(suggestion_type="Framework",
                                                       file_name=f"framework_{safe_slug(name, 'framework', 40)}.json",
                                                       file_content=payload, title_summary=f"Framework suggestion: {name.strip()}")
            (st.error if "❌" in message else st.success)(message)

