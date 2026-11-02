# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 2: Framework and Measures.

Theory organizes the module. Choose a framework (a theory, a lens, your own
framework, or an exploratory approach); the framework supplies constructs; each
construct gets measures (library instruments, researcher-written questions, or
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
from oem import recommend as R
from oem.app.common import (APP_DIR, context_search_terms, current_project,
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
        if base["frameworks"] and not base["constructs"]:
            base["constructs"] = P.framework_constructs(lib, base["frameworks"])
        if not base["relationships"]:
            base["relationships"] = P.default_relationships(lib, base["frameworks"], {c["id"] for c in base["constructs"]})
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


def _construct_label(lib, construct: dict) -> str:
    fid = construct.get("framework_id")
    source = lib.frameworks[fid]["label"].split(" (")[0] if fid in lib.frameworks else "your construct"
    return f"{construct['label']} — {source}"


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
TABS = ["🧭 Build your plan", "💡 Recommend a theory or framework", "📏 Recommend an instrument", "✏️ Suggest a correction"]


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    lib = library()
    st.header("2. Framework and Measures")
    st.caption(
        "Start from theory. Choose the framework that guides your study, and it supplies the constructs. Give each "
        "construct a measure (a library instrument, your own questions, or codes in a coding scheme), and the "
        "framework's expected relationships draw the diagram. The result is your variable plan and its codebook."
    )
    st.info("**Help grow the shared library.** Know a theory, conceptual model, or instrument that should be here? "
            "Use the **Recommend** tabs below. Each recommendation is reviewed before it is added for everyone.")
    plan_tab, framework_tab, instrument_tab, correction_tab = st.tabs(TABS)
    with plan_tab:
        _plan(lib, publish_disabled, publish_hint)
    with framework_tab:
        _recommend_framework(lib, publish_disabled, publish_hint)
    with instrument_tab:
        _recommend_instrument(lib, publish_disabled, publish_hint)
    with correction_tab:
        _suggest_correction(lib, publish_disabled, publish_hint)


def _plan(lib, publish_disabled: bool, publish_hint: str | None) -> None:
    base = _base(lib)
    v = st.session_state["m2_version"]
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
        help="Choose one or more. Pick 'My own conceptual framework' to define your own constructs, or "
             "'Exploratory or inductive' if constructs will emerge from the data.",
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
    st.caption(f"Don't see your theory or framework? Recommend it in the **{TABS[1]}** tab.")
    related = _related_studies(lib, plan["frameworks"])
    if related:
        with st.expander(f"Published studies using the same framework ({len(related)})"):
            for item in related:
                st.markdown(f"- **{item.get('study_title', 'Untitled')}**: "
                            + ", ".join((item.get("study_metadata") or {}).get("selected_theories", [])))

    # ------------------------------------------------------------ Step 2
    st.subheader("Step 2 · Constructs")
    st.caption("The framework supplies its constructs. Keep the ones your study addresses and add your own. "
               "Link a construct to the shared construct list when it means the same thing to you; that link is "
               "how studies find each other and how library instruments are found.")
    base_by_framework: dict[str, list[str]] = {}
    for c in base["constructs"]:
        base_by_framework.setdefault(c.get("framework_id") or "", []).append(c["id"])
    construct_labels = {c["label"]: cid for cid, c in sorted(lib.constructs.items(), key=lambda kv: kv[1]["label"])}
    construct_names = {cid: label for label, cid in construct_labels.items()}
    constructs: list[dict] = []
    for fid in plan["frameworks"]:
        available = P.framework_constructs(lib, [fid])
        if not available:
            continue
        by_key = {c["id"]: c for c in available}
        default = ([k for k in base_by_framework.get(fid, list(by_key)) if k in by_key]
                   if fid in base["frameworks"] else list(by_key))
        chosen = st.multiselect(
            f"Constructs from {lib.frameworks[fid]['label']}", list(by_key), default=default,
            format_func=lambda k, by_key=by_key: by_key[k]["label"] + (
                f"  ·  shared construct: {construct_names[by_key[k]['shared_construct_id']]}"
                if by_key[k].get("shared_construct_id") in construct_names else ""),
            key=f"m2_fc_{fid}_{v}")
        constructs += [by_key[k] for k in chosen]
    if any(c.get("shared_construct_id") for c in constructs):
        st.caption("Links from a theory's constructs to the shared construct list are provisional until the HuMeta "
                   "governance committee reviews them.")
    own_base = [c for c in base["constructs"] if not c.get("framework_id")]
    own_df = st.data_editor(
        pd.DataFrame([{"Construct": c["label"], "Definition": c.get("definition", ""),
                       "Shared construct (optional)": construct_names.get(c.get("shared_construct_id"))} for c in own_base],
                     columns=["Construct", "Definition", "Shared construct (optional)"]),
        num_rows="dynamic", use_container_width=True, key=f"m2_own_{v}",
        column_config={"Shared construct (optional)": st.column_config.SelectboxColumn(
            "Shared construct (optional)", options=list(construct_labels),
            help="Choose a shared construct only if it means the same thing as your construct.")},
    )
    st.caption("Your own constructs: for your own framework, a lens, or constructs emerging from exploratory work.")
    seen = {c["id"] for c in constructs}
    for row in own_df.to_dict(orient="records"):
        label = _s(row.get("Construct"))
        if not label:
            continue
        key_ = P.construct_key(None, label)
        if key_ in seen:
            continue
        seen.add(key_)
        constructs.append({"id": key_, "label": label, "framework_id": None,
                           "shared_construct_id": construct_labels.get(_s(row.get("Shared construct (optional)"))),
                           "definition": _s(row.get("Definition"))})
    plan["constructs"] = constructs
    construct_keys = {c["id"] for c in constructs}
    construct_display = {_construct_label(lib, c): c["id"] for c in constructs}
    construct_from_key = {k: label for label, k in construct_display.items()}

    # ------------------------------------------------------------ Step 3
    st.subheader("Step 3 · Measures and codes")
    st.caption(
        "Give each construct at least one measure: a library instrument or subscale, your own questions, or codes in "
        "a coding scheme (for texts, images, media, or interviews). **You decide whether a measure fits your construct "
        "as you define it.** Variable names are generated from the library and the construct, so studies using the "
        "same measure share names."
    )
    instrument_options = _instrument_options(lib)
    scale_labels = {s.label: sid for sid, s in lib.scales.items()}
    scale_names = {sid: label for label, sid in scale_labels.items()}
    kind_labels = {label: kind for kind, label in P.MEASURE_KINDS.items()}
    measures_df = st.data_editor(
        pd.DataFrame([{
            "Construct": construct_from_key.get(m.get("construct")),
            "Type": P.MEASURE_KINDS.get(m.get("kind")),
            "Library instrument": _instrument_label(instrument_options, m) if m.get("kind") == "instrument" else None,
            "Question, or code definition": m.get("text") or "",
            "Label (code name or item label)": m.get("label") or "",
            "Response scale": scale_names.get(m.get("scale_id")),
            "Variable name (optional)": m.get("name") or "",
        } for m in base["measures"]], columns=["Construct", "Type", "Library instrument", "Question, or code definition",
                                               "Label (code name or item label)", "Response scale", "Variable name (optional)"]),
        num_rows="dynamic", use_container_width=True, key=f"m2_measures_{v}",
        column_config={
            "Construct": st.column_config.SelectboxColumn("Construct", options=list(construct_display), required=True),
            "Type": st.column_config.SelectboxColumn("Type", options=list(kind_labels), required=True),
            "Library instrument": st.column_config.SelectboxColumn("Library instrument", options=list(instrument_options)),
            "Response scale": st.column_config.SelectboxColumn("Response scale", options=list(scale_labels)),
        },
    )
    measures = []
    for row in measures_df.to_dict(orient="records"):
        if not _s(row.get("Construct")) and not _s(row.get("Type")):
            continue
        iid, vid, did = instrument_options.get(_s(row.get("Library instrument")), (None, None, None))
        measures.append({"construct": construct_display.get(_s(row.get("Construct"))), "kind": kind_labels.get(_s(row.get("Type"))),
                         "instrument_id": iid, "version_id": vid, "dimension_id": did,
                         "name": _s(row.get("Variable name (optional)")),
                         "label": _s(row.get("Label (code name or item label)")),
                         "text": _s(row.get("Question, or code definition")),
                         "scale_id": scale_labels.get(_s(row.get("Response scale")))})
    plan["measures"] = measures

    in_plan = {(x["construct"], x["instrument_id"], x["dimension_id"]) for x in measures}
    candidates = [c for c in P.candidate_measures(lib, constructs)
                  if (c["construct"], c["instrument_id"], c["dimension_id"]) not in in_plan]
    if candidates:
        with st.expander(f"Library instruments to consider ({len(candidates)})", expanded=True):
            st.caption("These library instruments are recorded as measuring the shared construct you linked. Read what "
                       "each part was developed to measure and decide whether it fits **your** construct. Tick the ones "
                       "to add. Instrument-to-construct mappings are provisional until the HuMeta governance committee "
                       "reviews them.")
            cand_df = st.data_editor(
                pd.DataFrame([{
                    "Add": False,
                    "Your construct": construct_from_key.get(c["construct"]),
                    "Instrument": lib.instruments[c["instrument_id"]]["name"],
                    "Part": c["part"],
                    "Developed to measure": ", ".join(c["measures"]),
                    "Mapping status": P.MAPPING_STATUS[c["mapping_status"]].split(" (")[0],
                } for c in candidates]),
                disabled=["Your construct", "Instrument", "Part", "Developed to measure", "Mapping status"],
                hide_index=True, use_container_width=True, key=f"m2_candidates_{v}",
                column_config={"Add": st.column_config.CheckboxColumn("Add", help="Add this measure for your construct")},
            )
            picked = [P.as_measure(c) for c, row in zip(candidates, cand_df.to_dict(orient="records")) if row.get("Add") is True]
            if st.button(f"Add {len(picked)} selected measure(s)", disabled=not picked, key=f"m2_add_lib_{v}"):
                _rebase({**plan, "measures": measures + picked, "relationships": base["relationships"]})
    st.caption(f"Know an instrument that measures one of your constructs but is not in the library? Recommend it in the "
               f"**{TABS[2]}** tab.")
    unmeasured = [c["label"] for c in constructs if c["id"] not in {m["construct"] for m in measures}]
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
                status = P.MAPPING_STATUS[P.mapping_status(inst)]
                st.markdown(f"**{inst['name']}**. {text_ok}. Access: {access.get('terms_summary', access.get('access_type', ''))} "
                            f"{cite} *Construct mapping: {status}.*")

    # ------------------------------------------------------------ Step 4
    st.subheader("Step 4 · Relationships and diagram")
    st.caption("Expected relationships between constructs start from the framework. Edit them, add your own, and note hypotheses.")
    rel_df = st.data_editor(
        pd.DataFrame([{"From": construct_from_key.get(r["from"]), "To": construct_from_key.get(r["to"]),
                       "Relationship": r.get("relationship", ""), "Hypothesis or rationale": r.get("hypothesis", "")}
                      for r in base["relationships"] if r["from"] in construct_keys and r["to"] in construct_keys],
                     columns=["From", "To", "Relationship", "Hypothesis or rationale"]),
        num_rows="dynamic", use_container_width=True, key=f"m2_rel_{v}",
        column_config={"From": st.column_config.SelectboxColumn("From", options=list(construct_display)),
                       "To": st.column_config.SelectboxColumn("To", options=list(construct_display))},
    )
    plan["relationships"] = [
        {"from": construct_display[_s(r.get("From"))], "to": construct_display[_s(r.get("To"))],
         "relationship": _s(r.get("Relationship")), "hypothesis": _s(r.get("Hypothesis or rationale"))}
        for r in rel_df.to_dict(orient="records") if _s(r.get("From")) in construct_display and _s(r.get("To")) in construct_display]
    defaults = [r for r in P.default_relationships(lib, plan["frameworks"], construct_keys)
                if (r["from"], r["to"]) not in {(x["from"], x["to"]) for x in plan["relationships"]}]
    if defaults and st.button(f"Add the framework's {len(defaults)} expected relationship(s)", key=f"m2_paths_{v}"):
        _rebase({**plan, "relationships": plan["relationships"] + defaults})
    if constructs:
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
        st.markdown("**Alignment: construct → measure → variables**")
        st.dataframe(pd.DataFrame(P.alignment(lib, plan)), use_container_width=True, hide_index=True)
        st.markdown(f"**Codebook:** {len(book)} variables for {len(constructs)} constructs.")
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
                                                               *[c["label"] for c in plan["constructs"]]])),
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
            st.caption("Shares the framework, constructs, and measures, with no item text, data, or participant information.")
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


# -------------------------------------------------------- recommendations
def _submission_notice() -> None:
    public_submission_warning()
    st.caption("Your name from sign-in appears on the submission. Recommendations land in the project's "
               "`suggestions/` folder, and a maintainer checks the source before adding anything to the library.")


def _send(rec: dict, issues: list[str]) -> None:
    if issues:
        for issue in issues:
            st.error(issue)
        return
    path, content = R.file_for(rec)
    with st.spinner("Opening a pull request for maintainer review..."):
        message = open_review_pull_request(suggestion_type=f"{rec['recommendation'].capitalize()} recommendation",
                                           title_summary=R.title_for(rec), files={path: content},
                                           description=R.pr_description(rec))
    (st.error if "❌" in message else st.success)(message)


def _recommend_framework(lib, publish_disabled: bool, publish_hint: str | None) -> None:
    st.subheader("Recommend a theory, conceptual model, or framework")
    st.caption("Theories, lenses, and frameworks recommended here can be added to Step 1 for everyone, with their "
               "constructs and expected relationships. Check the current list in Step 1 first. Links you propose from "
               "its constructs to shared constructs or instruments are decided by the HuMeta governance committee.")
    _submission_notice()
    construct_labels = {c["label"]: cid for cid, c in sorted(lib.constructs.items(), key=lambda kv: kv[1]["label"])}
    with st.form("m2_recommend_framework", clear_on_submit=False):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name *", placeholder="e.g., Situated Expectancy-Value Theory")
        kind = c2.selectbox("What kind is it? *", list(R.FRAMEWORK_KINDS), format_func=R.FRAMEWORK_KINDS.get)
        description = st.text_area("Describe it in a sentence or two *")
        st.markdown("**Constructs** (required for theories): one row per construct")
        constructs_df = st.data_editor(
            pd.DataFrame([{"Construct": "", "Definition": "", "Same as shared construct (optional)": None,
                           "Instruments that measure it (optional)": ""}]),
            num_rows="dynamic", use_container_width=True, key="m2_rec_fw_constructs",
            column_config={"Same as shared construct (optional)": st.column_config.SelectboxColumn(
                "Same as shared construct (optional)", options=list(construct_labels))})
        relationships = st.text_area("Expected relationships, one per line, as 'A -> B: relationship' (optional)",
                                     placeholder="Expectancy -> Achievement choices: predicts")
        c1, c2 = st.columns(2)
        citation = c1.text_area("Key citation *", height=90)
        doi = c2.text_input("DOI (optional)", placeholder="10.xxxx/xxxxx")
        fields = c2.multiselect("Fields where it is used", ["education", "social_sciences", "humanities", "arts", "other_field"],
                                format_func=lambda f: f.replace("_", " ").capitalize())
        rationale = st.text_area("Why should it be in the list? (optional)")
        consent = st.checkbox("I confirm this recommendation contains no confidential information and may be published.")
        submitted = st.form_submit_button("Submit recommendation", type="primary", disabled=publish_disabled, help=publish_hint)
    if submitted:
        rows = [{"construct": r.get("Construct"), "definition": r.get("Definition"),
                 "shared_construct_id": construct_labels.get(_s(r.get("Same as shared construct (optional)"))),
                 "instruments": r.get("Instruments that measure it (optional)")}
                for r in constructs_df.to_dict(orient="records")]
        rec = R.framework_recommendation(name=name, kind=kind, description=description, citation=citation, doi=doi,
                                         fields=fields, constructs=rows, relationships=relationships, rationale=rationale)
        issues = R.framework_problems(rec, lib) + ([] if consent else ["Tick the confirmation box."])
        _send(rec, issues)


def _recommend_instrument(lib, publish_disabled: bool, publish_hint: str | None) -> None:
    st.subheader("Recommend an instrument")
    st.caption("Instruments recommended here can be added to the library. Say exactly what each part of the instrument "
               "measures: the whole instrument, or each subscale and its items. These are proposed mappings; the HuMeta "
               "governance committee decides which constructs an instrument maps to, and researchers decide whether it "
               "fits their own construct. Do **not** paste item text unless you are the developer and the license "
               "allows it.")
    _submission_notice()
    construct_labels = {c["label"]: cid for cid, c in sorted(lib.constructs.items(), key=lambda kv: kv[1]["label"])}
    plan_constructs = [c["label"] for c in (st.session_state.get("m2_pending") or {}).get("constructs", [])]
    with st.form("m2_recommend_instrument", clear_on_submit=False):
        c1, c2, c3 = st.columns([3, 1, 2])
        name = c1.text_input("Instrument name *")
        acronym = c2.text_input("Acronym")
        relationship = c3.selectbox("Your relationship to it *", list(R.RELATIONSHIPS), format_func=R.RELATIONSHIPS.get)
        c1, c2 = st.columns(2)
        citation = c1.text_area("Primary citation *", height=90)
        doi = c2.text_input("DOI (optional)", placeholder="10.xxxx/xxxxx")
        url = c2.text_input("Link to the instrument or its manual (optional)")
        st.markdown("**What does each part measure?** \\* One row for the whole instrument, or one row per subscale.")
        alignment_df = st.data_editor(
            pd.DataFrame([{"Part (whole instrument or subscale)": "Whole instrument", "Items (numbers or count)": "",
                           "Measures (shared construct)": None, "Or a construct not on the list": "",
                           "Theory construct (optional, e.g., SDT: Competence)": ""}]),
            num_rows="dynamic", use_container_width=True, key="m2_rec_inst_alignment",
            column_config={"Measures (shared construct)": st.column_config.SelectboxColumn(
                "Measures (shared construct)", options=list(construct_labels))})
        construct = st.selectbox("Construct in your plan that it measures (optional)", ["", *plan_constructs])
        c1, c2, c3 = st.columns(3)
        respondents = c1.text_input("Who responds?", placeholder="e.g., undergraduate students")
        item_count = c2.text_input("Total number of items")
        response_format = c3.text_input("Response format", placeholder="e.g., 5-point agreement")
        populations = st.text_input("Populations or settings it has been validated with")
        c1, c2 = st.columns(2)
        access = c1.selectbox("How can researchers get it? *", list(R.ACCESS_OPTIONS), format_func=R.ACCESS_OPTIONS.get)
        access_details = c2.text_input("License or terms of use (if known)")
        evidence = st.text_area("Reliability and validity evidence, with citations (optional)")
        permission = st.checkbox("I am a developer and I am willing to share item text under an open license "
                                 "(a maintainer will contact you to confirm).")
        notes = st.text_area("Anything else (versions, translations, adaptations)?")
        consent = st.checkbox("I confirm this recommendation contains no item text I lack permission to share, and no "
                              "confidential information.")
        submitted = st.form_submit_button("Submit recommendation", type="primary", disabled=publish_disabled, help=publish_hint)
    if submitted:
        rows = [{"part": r.get("Part (whole instrument or subscale)"), "items": r.get("Items (numbers or count)"),
                 "shared_construct_id": construct_labels.get(_s(r.get("Measures (shared construct)"))),
                 "other_construct": r.get("Or a construct not on the list"),
                 "theory_construct": r.get("Theory construct (optional, e.g., SDT: Competence)")}
                for r in alignment_df.to_dict(orient="records")]
        rec = R.instrument_recommendation(
            name=name, acronym=acronym, citation=citation, doi=doi, url=url, alignment=rows,
            respondents=respondents, populations=populations, item_count=item_count,
            response_format=response_format, access=access, access_details=access_details, evidence=evidence,
            relationship=relationship, item_text_permission=permission, construct=construct, notes=notes)
        issues = R.instrument_problems(rec, lib) + ([] if consent else ["Tick the confirmation box."])
        _send(rec, issues)


def _suggest_correction(lib, publish_disabled: bool, publish_hint: str | None) -> None:
    st.subheader("Suggest a correction")
    st.caption("Fix a citation, add a missing construct or relationship to a theory, link a construct to a different "
               "construct, or correct an instrument's details.")
    _submission_notice()
    targets = {f"Framework: {f['label']}": ("framework", fid) for fid, f in sorted(lib.frameworks.items(), key=lambda kv: kv[1]["label"])}
    targets.update({f"Instrument: {i['name']}": ("instrument", iid) for iid, i in sorted(lib.instruments.items(), key=lambda kv: kv[1]["name"])})
    targets.update({f"Construct: {c['label']}": ("construct", cid) for cid, c in sorted(lib.constructs.items(), key=lambda kv: kv[1]["label"])})
    with st.form("m2_correction", clear_on_submit=False):
        target = st.selectbox("What needs correcting? *", list(targets))
        change = st.text_area("What should change, and why? *")
        source = st.text_input("Source that supports the change (citation or link)")
        consent = st.checkbox("I confirm this suggestion contains no confidential information and may be published.")
        submitted = st.form_submit_button("Submit correction", type="primary", disabled=publish_disabled, help=publish_hint)
    if submitted:
        kind, tid = targets[target]
        rec = R.correction(target_kind=kind, target_id=tid, change=change, source=source)
        _send(rec, R.correction_problems(rec) + ([] if consent else ["Tick the confirmation box."]))
