# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 2: Theory and Measures.

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

from oem import metacode
from oem import plan as P
from oem import profile
from oem import evidence as EV
from oem import recommend as R
from oem.vocab import library_page_url
from oem.app.common import (APP_DIR, context_search_terms, current_project,
                            load_published_summaries, open_review_pull_request, public_submission_warning,
                            navigate_to_module, render_project_download, safe_slug)
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
TABS = ["🧭 Build your plan", "💡 Suggest to the library"]
SUGGESTIONS = {"framework": "A theory or framework", "instrument": "An instrument", "correction": "A correction"}


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    lib = library()
    st.header("2. Theory and Measures")
    st.caption(
        "Plan what your study measures: a theory if you have one, the constructs you study, measures for them, and "
        "other variables such as demographics. The result is your variable plan and its codebook. Save it in Step 6 "
        "to carry it into Module 3."
    )
    plan_tab, suggest_tab = st.tabs(TABS)
    with plan_tab:
        _plan(lib, publish_disabled, publish_hint)
    with suggest_tab:
        st.caption("Know a theory, conceptual model, or instrument that should be in the shared library, or see "
                   "something to fix? Each suggestion is reviewed before it is added for everyone.")
        kind = st.radio("What would you like to suggest?", list(SUGGESTIONS), format_func=SUGGESTIONS.get,
                        horizontal=True, key="m2_suggest_kind")
        {"framework": _recommend_framework, "instrument": _recommend_instrument,
         "correction": _suggest_correction}[kind](lib, publish_disabled, publish_hint)


FIELD_FILTERS = {"": "All fields", "education": "Education", "social_sciences": "Social sciences",
                 "humanities": "Humanities", "arts": "Arts"}
KIND_FILTERS = {"": "All kinds", "theory": "Theories (with constructs and relationships)",
                "lens": "Lenses (interpretive perspectives)"}
BROWSE_PAGE = 12


def _add_framework(picker_key: str, fid: str) -> None:
    chosen = list(st.session_state.get(picker_key) or [])
    if fid not in chosen:
        st.session_state[picker_key] = chosen + [fid]


def _discipline_label(prof, term_id: str) -> str:
    """'Human society › Sociology' for a group, 'Human society (all)' for a division."""
    term = prof.term("discipline", term_id)
    division = term.get("division")
    return f"{prof.label('discipline', division).removesuffix(' (all)')} › {term['label']}" if division else term["label"]


def _browse_frameworks(lib, picker_key: str, v: int) -> None:
    """Browse the framework library by field, kind, discipline, and search; preview and add."""
    record = current_record() or {}
    saved_fields = [f for f in ((record.get("study") or {}).get("fields") or []) if f in FIELD_FILTERS]
    prof = profile.load()
    disciplines = {d: _discipline_label(prof, d) for d in prof.active_ids("discipline")}
    with st.container(border=True):
        st.markdown("**Browse the framework library**")
        c1, c2, c3, c4 = st.columns([1, 1.3, 1.2, 1.5])
        field = c1.selectbox("Field", list(FIELD_FILTERS), format_func=FIELD_FILTERS.get, key=f"m2_browse_field_{v}",
                             index=list(FIELD_FILTERS).index(saved_fields[0]) if len(saved_fields) == 1 else 0,
                             help="Starts from the research field in your Module 1 study profile.")
        kind = c2.selectbox("Kind", list(KIND_FILTERS), format_func=KIND_FILTERS.get, key=f"m2_browse_kind_{v}")
        fos_prefix = {"education": "5.3", "social_sciences": "5", "humanities": "6", "arts": "6.4"}.get(field, "")
        in_field = [d for d in disciplines if str(prof.term("discipline", d).get("fos", "")).startswith(fos_prefix)]
        counts = {d: len(P.browse_frameworks(lib, field or None, kind or None, d)) - 2 for d in in_field}  # minus own/exploratory
        discipline = c3.selectbox("Discipline (ANZSRC)", [""] + in_field, key=f"m2_browse_disc_{v}",
                                  format_func=lambda d: f"{disciplines[d]} ({counts[d]})" if d else "All disciplines",
                                  help="Disciplines follow the ANZSRC 2020 Fields of Research. The number is how many "
                                       "frameworks in the library are tagged with it.")
        query = c4.text_input("Search", key=f"m2_browse_q_{v}", placeholder="name, idea, construct, or author")
        found = [fid for fid in P.browse_frameworks(lib, field or None, kind or None, discipline or None, query)
                 if lib.frameworks[fid]["kind"] in ("theory", "lens")]
        total = sum(1 for fw in lib.frameworks.values() if fw["kind"] in ("theory", "lens"))
        st.caption(f"{len(found)} of {total} theories and lenses. Open one to see its constructs and citation. "
                   "**Draft**: every framework still needs review by experts in its field; suggest changes in the correction tab.")
        show_all = len(found) > BROWSE_PAGE and st.toggle(f"Show all {len(found)}", key=f"m2_browse_all_{v}")
        chosen = set(st.session_state.get(picker_key) or [])
        for fid in found if show_all else found[:BROWSE_PAGE]:
            fw = lib.frameworks[fid]
            title = f"{fw['label']}  ·  {KIND_PREFIX[fw['kind']]}" + ("  ·  Draft" if fw.get("status") == "draft" else "") \
                + ("  ·  ✓ in your plan" if fid in chosen else "")
            with st.expander(title):
                st.markdown(fw["description"])
                if fw.get("constructs"):
                    st.markdown("**Constructs:** " + ", ".join(c["label"] for c in fw["constructs"])
                                + (f"  \n**Expected relationships:** {len(fw.get('paths', []))}" if fw.get("paths") else ""))
                else:
                    st.caption("A lens: you describe the constructs and ideas you draw from it in Step 2.")
                if fw.get("disciplines"):
                    st.caption("Used in: " + ", ".join(disciplines.get(d, d) for d in fw["disciplines"]))
                cite = fw.get("citation") or ""
                if fw.get("doi"):
                    cite += f" [doi:{fw['doi']}](https://doi.org/{fw['doi']})"
                if cite:
                    st.caption(f"Key source: {cite}")
                if fw.get("kind") not in ("own", "exploratory"):
                    st.caption(f"[Library page]({library_page_url(lib, 'frameworks', fw['id'])}): constructs, relationships, "
                               "and instruments that measure them")
                if fw.get("status") == "draft":
                    st.caption("Draft: please check the constructs and relationships, and suggest changes in the "
                               f"**{TABS[1]}** tab.")
                st.button("✓ In your plan" if fid in chosen else "Add to my plan", key=f"m2_add_{fid}_{v}",
                          disabled=fid in chosen, on_click=_add_framework, args=(picker_key, fid))
        if not found:
            st.info(f"No match. Try another field or search, or recommend it in the **{TABS[1]}** tab.")


def _plan(lib, publish_disabled: bool, publish_hint: str | None) -> None:
    base = _base(lib)
    v = st.session_state["m2_version"]
    record = current_record()
    st.caption("**Every step can be skipped.** Do what is easy now and come back to the rest. To save, you need at "
               "least one construct (Step 2) or one variable (Step 4).")
    if record is None:
        st.info("Tip: save your study profile in Module 1 first. This module then suggests variables for your study.")

    plan = P.empty_plan()
    for later in ("standard_variables", "timepoints", "external_variables", "relationships", "positions", "narrative"):
        plan[later] = base.get(later) or plan[later]
    kinds = {fid: f["kind"] for fid, f in lib.frameworks.items()}

    # ------------------------------------------------------------ Step 1
    st.subheader("Step 1 · Theory or framework (optional)")
    st.caption("If a theory guides your study, choose it here and it fills in your constructs in Step 2. "
               "No theory, or not sure? Skip to Step 2.")
    picker_key = f"m2_frameworks_{v}"
    if picker_key not in st.session_state:
        st.session_state[picker_key] = [f for f in base["frameworks"] if f in lib.frameworks]
    n_theories = sum(1 for fw in lib.frameworks.values() if fw["kind"] in ("theory", "lens"))
    if st.toggle(f"Browse the theory library ({n_theories} theories and lenses, by field)", key=f"m2_browse_open_{v}"):
        _browse_frameworks(lib, picker_key, v)
    plan["frameworks"] = st.multiselect(
        "Your theory or framework", P.browse_frameworks(lib), key=picker_key, placeholder="None (skip)",
        format_func=lambda fid: f"{KIND_PREFIX[kinds[fid]]}: {lib.frameworks[fid]['label']}",
        help="Add theories from the library above, or type a name here. Working from your own framework? Choose "
             "'My own conceptual framework'.",
    )
    for fid in plan["frameworks"]:
        fw = lib.frameworks[fid]
        if fw["kind"] in ("theory", "lens"):
            st.caption(f"**{fw['label']}.** {fw['description']} *{fw.get('citation') or 'Cite the specific work you draw on.'}*"
                       + (" (Draft: needs expert check.)" if fw.get("status") == "draft" else ""))
    if plan["frameworks"]:
        plan["framework_description"] = st.text_area(
            "How does it guide your study? (optional)", base["framework_description"], key=f"m2_fdesc_{v}",
            help="Especially useful for your own framework or a lens: describe it and the ideas it brings.")
    else:
        plan["framework_description"] = base["framework_description"]
    st.caption(f"Don't see your theory? Recommend it in the **{TABS[1]}** tab.")
    related = _related_studies(lib, plan["frameworks"])
    if related:
        with st.expander(f"Published studies using the same framework ({len(related)})"):
            for item in related:
                st.markdown(f"- **{item.get('study_title', 'Untitled')}**: "
                            + ", ".join((item.get("study_metadata") or {}).get("selected_theories", [])))

    # ------------------------------------------------------------ Step 2
    st.subheader("Step 2 · What you want to study (constructs)")
    st.caption("Constructs are the ideas you measure or describe, such as interest or sense of belonging. "
               + ("Your theory supplied the ones below: keep those your study addresses. " if plan["frameworks"] else "")
               + "Pick any from the shared list, which links them to library instruments and to other studies, "
               "or name your own.")
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
            f"From {lib.frameworks[fid]['label']}", list(by_key), default=default,
            format_func=lambda k, by_key=by_key: by_key[k]["label"] + (
                f"  ·  shared construct: {construct_names[by_key[k]['shared_construct_id']]}"
                if by_key[k].get("shared_construct_id") in construct_names else ""),
            key=f"m2_fc_{fid}_{v}")
        constructs += [by_key[k] for k in chosen]
    from_theory = {c.get("shared_construct_id") for c in constructs}
    shared_options = [cid for cid in construct_names if cid not in from_theory]
    picked = st.multiselect(
        "From the shared construct list", shared_options, key=f"m2_shared_{v}", placeholder="Search constructs",
        default=[c["shared_construct_id"] for c in base["constructs"]
                 if P.is_shared_list_construct(lib, c) and c["shared_construct_id"] in shared_options],
        format_func=construct_names.get,
        help="Choose a construct if it means the same thing as what you want to study. Library instruments for it "
             "are then suggested in Step 3.")
    seen = {c["id"] for c in constructs}
    for sid in picked:
        c = P.shared_list_construct(lib, sid)
        if c["id"] not in seen:
            seen.add(c["id"])
            constructs.append(c)
    own_base = [c for c in base["constructs"] if not c.get("framework_id") and not P.is_shared_list_construct(lib, c)]
    with st.expander(f"Name your own constructs ({len(own_base)})" if own_base else "Name your own constructs (not on the list)",
                     expanded=bool(own_base)):
        own_df = st.data_editor(
            pd.DataFrame([{"Construct": c["label"], "Definition": c.get("definition", ""),
                           "Shared construct (optional)": construct_names.get(c.get("shared_construct_id"))}
                          for c in own_base],
                         columns=["Construct", "Definition", "Shared construct (optional)"]),
            num_rows="dynamic", use_container_width=True, key=f"m2_own_{v}",
            column_config={"Shared construct (optional)": st.column_config.SelectboxColumn(
                "Shared construct (optional)", options=list(construct_labels),
                help="Choose a shared construct only if it means the same thing as your construct.")},
        )
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
    if any(c.get("shared_construct_id") and c.get("framework_id") for c in constructs):
        st.caption("Links from a theory's constructs to the shared construct list are provisional until the HuMeta "
                   "governance committee reviews them.")
    plan["constructs"] = constructs
    construct_keys = {c["id"] for c in constructs}
    construct_display = {_construct_label(lib, c): c["id"] for c in constructs}
    construct_from_key = {k: label for label, k in construct_display.items()}

    # ------------------------------------------------------------ Step 3
    st.subheader("Step 3 · Measures (optional)")
    st.caption(
        "Add a measure where you have one: a library instrument, your own questions, or codes in a coding scheme. "
        "**No measure yet, or not sure what fits? Skip it.** Constructs without a measure stay in your plan and "
        "still go to Module 3; you can add measures later. You decide whether a measure fits your construct."
    )
    measures, skipped = [], 0
    instrument_options = _instrument_options(lib)
    in_base = {(x.get("construct"), x.get("instrument_id"), x.get("dimension_id")) for x in base["measures"]}
    candidates = [c for c in P.candidate_measures(lib, constructs)
                  if (c["construct"], c["instrument_id"], c["dimension_id"]) not in in_base]
    if candidates:
        with st.expander(f"Library instruments for your constructs ({len(candidates)})", expanded=not base["measures"]):
            st.caption("These library instruments are recorded as measuring the shared constructs in your plan. Read "
                       "what each part was developed to measure and tick the ones that fit. Instrument-to-construct "
                       "mappings are provisional until the HuMeta governance committee reviews them.")
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
            picked_measures = [P.as_measure(c) for c, row in zip(candidates, cand_df.to_dict(orient="records"))
                               if row.get("Add") is True]
    else:
        picked_measures = []
        if constructs and not any(c.get("shared_construct_id") for c in constructs):
            st.caption("Library instruments are suggested for constructs from the shared list (Step 2).")
    search_picks, new_constructs = _search_library(lib, constructs, construct_display, construct_from_key, v)
    scale_labels = {s.label: sid for sid, s in lib.scales.items()}
    scale_names = {sid: label for label, sid in scale_labels.items()}
    kind_labels = {label: kind for kind, label in P.MEASURE_KINDS.items() if kind != "published"}
    published_base = [m for m in base["measures"] if m.get("kind") == "published"]
    n_table = len(base["measures"]) - len(published_base)
    with st.expander(f"Your measures ({n_table})" if n_table
                     else "Add a measure yourself (your own questions, codes, or another instrument)",
                     expanded=bool(n_table)):
        measures_df = st.data_editor(
            pd.DataFrame([{
                "Construct": construct_from_key.get(m.get("construct")),
                "Type": P.MEASURE_KINDS.get(m.get("kind")),
                "Library instrument": _instrument_label(instrument_options, m) if m.get("kind") == "instrument" else None,
                "Question, or code definition": m.get("text") or "",
                "Label (code name or item label)": m.get("label") or "",
                "Response scale": scale_names.get(m.get("scale_id")),
                "Target (optional)": m.get("target") or "",
                "Variable name (optional)": m.get("name") or "",
            } for m in base["measures"] if m.get("kind") != "published"],
                columns=["Construct", "Type", "Library instrument", "Question, or code definition",
                                                   "Label (code name or item label)", "Response scale", "Target (optional)",
                                                   "Variable name (optional)"]),
            num_rows="dynamic", use_container_width=True, key=f"m2_measures_{v}",
            column_config={
                "Construct": st.column_config.SelectboxColumn("Construct", options=list(construct_display)),
                "Type": st.column_config.SelectboxColumn("Type", options=list(kind_labels)),
                "Library instrument": st.column_config.SelectboxColumn("Library instrument", options=list(instrument_options)),
                "Response scale": st.column_config.SelectboxColumn("Response scale", options=list(scale_labels)),
                "Target (optional)": st.column_config.TextColumn(
                    "Target (optional)", help="What the measure is about, in a word or two: e.g. Vote, Recycling, "
                    "Physics. Added to the metadata code so studies with the same target can be found."),
            },
        )
    for row in measures_df.to_dict(orient="records"):
        construct_id = construct_display.get(_s(row.get("Construct")))
        kind = kind_labels.get(_s(row.get("Type")))
        iid, vid, did = instrument_options.get(_s(row.get("Library instrument")), (None, None, None))
        text, label = _s(row.get("Question, or code definition")), _s(row.get("Label (code name or item label)"))
        if not any(_s(x) for x in row.values()):
            continue
        # Unfinished rows are left out rather than blocking the save.
        if not construct_id or not kind or (kind == "instrument" and not iid) or (kind != "instrument" and not (text or label)):
            skipped += 1
            continue
        measures.append({"construct": construct_id, "kind": kind, "instrument_id": iid if kind == "instrument" else None,
                         "version_id": vid if kind == "instrument" else None,
                         "dimension_id": did if kind == "instrument" else None,
                         "name": _s(row.get("Variable name (optional)")), "label": label, "text": text,
                         "scale_id": scale_labels.get(_s(row.get("Response scale"))),
                         "target": _s(row.get("Target (optional)"))})
    measures += _published_instruments(published_base, construct_display, construct_from_key, constructs, v)
    skipped += st.session_state.pop("m2_published_skipped", 0)
    if skipped:
        st.caption(f"{skipped} unfinished row(s) are left out of the plan until they have a construct and a measure: "
                   "a library instrument, a question, or a published instrument's name with its first author and "
                   "year or DOI.")
    plan["measures"] = measures
    picked_measures = picked_measures + search_picks
    if picked_measures and st.button(f"Add {len(picked_measures)} selected instrument(s)", key=f"m2_add_lib_{v}",
                                     type="primary"):
        _rebase({**plan, "constructs": plan["constructs"] + new_constructs,
                 "measures": measures + picked_measures, "standard_variables": base["standard_variables"],
                 "timepoints": base["timepoints"], "relationships": base["relationships"],
                 "narrative": base.get("narrative", "")})
    unmeasured = [c["label"] for c in constructs if c["id"] not in {m["construct"] for m in measures}]
    if unmeasured and measures:
        st.caption("No measure yet (fine to leave for later): " + ", ".join(unmeasured))
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
                            f"{cite} *Construct mapping: {status}.* "
                            f"[Library page]({library_page_url(lib, 'instruments', iid)})")
                prof = EV.profile(lib, iid)
                st.caption("Evidence profile: " + EV.summary_line(prof)
                           + (". " + " ".join(prof.flags) if prof.flags else ""))

    # ------------------------------------------------------------ Step 4
    st.subheader("Step 4 · Other variables to collect")
    suggested = P.suggest_variables(lib, record)
    st.caption("Demographic and other standard variables, with shared names and codes so they match across studies. "
               "Tick the ones you will collect" + (", starting with those suggested from your study profile (Module 1)."
                                                   if suggested else "."))
    order = list(suggested) + [n for n in lib.standard_variables if n not in suggested]
    chosen_std = set()
    cols = st.columns(2)
    for i, name in enumerate(order):
        sv = lib.standard_variables[name]
        with cols[i % 2]:
            if st.checkbox(sv["label"] + ("  ·  suggested" if name in suggested else ""),
                           value=name in base["standard_variables"], key=f"m2_std_{name}_{v}", help=sv.get("notes")):
                chosen_std.add(name)
            if name in suggested:
                st.caption(suggested[name])
            links = [f"[ICPSR: {sv['icpsr_term']['term']}]({sv['icpsr_term']['url']})" if sv.get("icpsr_term") else "",
                     f"[US CIP codes (NCES)]({sv['code_list']['url']})" if sv.get("code_list") else ""]
            if any(links):
                st.caption("Wording and codes: " + " · ".join(x for x in links if x))
    plan["standard_variables"] = [n for n in lib.standard_variables if n in chosen_std]
    plan["external_variables"] = _icpsr_variables(base, v)
    suggested_tp = P.suggest_timepoints(record)
    plan["timepoints"] = st.multiselect(
        "Do you measure more than once? Timepoints (optional)", list(P.naming.TIMEPOINT_SUFFIXES),
        default=base["timepoints"], key=f"m2_tp_{v}", placeholder="Once only (skip)",
        help="Each measured variable is repeated with this suffix, e.g. _pre and _post.")
    if suggested_tp and not plan["timepoints"] and measures:
        c1, c2 = st.columns([3, 1])
        c1.caption(f"Your study design suggests measuring at: {', '.join(suggested_tp)}.")
        if c2.button("Use these", key=f"m2_use_tp_{v}"):
            _rebase({**plan, "timepoints": suggested_tp, "relationships": base["relationships"],
                     "narrative": base.get("narrative", "")})

    # ------------------------------------------------------------ Step 5
    st.subheader("Step 5 · How your constructs relate (optional)")
    narrative_base = base.get("narrative", "")
    if len(constructs) < 2:
        st.caption("With two or more constructs you can show how they relate. Add one below, or skip this step.")
        plan["relationships"] = [r for r in base["relationships"] if r["from"] in construct_keys and r["to"] in construct_keys]
        plan["positions"] = {k: xy for k, xy in (base.get("positions") or {}).items() if k in construct_keys}
        plan["narrative"] = narrative_base
    else:
        if plan["frameworks"]:
            st.caption("The relationships your theory expects are already filled in.")
        st.info(
            "**You can change the relationships in two ways. Use either one; they stay in sync.**\n\n"
            "**1. On the diagram:** **drag a box** to move it. **To add a relationship**, drag from the right edge "
            "of one box to the left edge of another. **To remove one**, right-click its arrow and choose "
            "**Delete Edge**. A two-headed arrow means each construct influences the other.\n\n"
            "**2. In the table** (*Edit relationships as a table*, below the diagram): add, change, or delete rows, "
            "and describe each relationship and your hypothesis.")
        diagram_area = st.container()  # drawn after the table, so table edits show at once
        with st.expander("Edit relationships as a table"):
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
            for r in rel_df.to_dict(orient="records")
            if _s(r.get("From")) in construct_display and _s(r.get("To")) in construct_display]
        missing = P.missing_theory_relationships(lib, plan, {c["id"] for c in base["constructs"]})
        if missing["new"]:
            # A construct was just added (e.g. a theory was chosen): include its expected relationships.
            _rebase({**plan, "relationships": plan["relationships"] + missing["new"], "narrative": narrative_base})
        positions = {**P.default_positions(plan),
                     **{k: xy for k, xy in (base.get("positions") or {}).items() if k in construct_keys}}
        with diagram_area:
            drawn = _diagram_editor(plan, positions, construct_from_key, v)
            if drawn is None:  # the interactive diagram is not available: show the picture
                plan["positions"] = positions
                st.graphviz_chart(P.diagram_dot(lib, plan), use_container_width=True)
            else:
                edges, plan["positions"] = drawn
                if set(edges) != {(r["from"], r["to"]) for r in plan["relationships"]}:
                    # Arrows drawn or deleted on the diagram: update the relationships (and the table).
                    _rebase({**plan, "relationships": P.relationships_from_edges(plan["relationships"], edges),
                             "narrative": narrative_base})
            if missing["removed"] and st.button(f"Restore the theory's {len(missing['removed'])} removed relationship(s)",
                                                key=f"m2_paths_{v}"):
                _rebase({**plan, "relationships": plan["relationships"] + missing["removed"], "narrative": narrative_base})
        with st.expander("Conceptual framework narrative (optional)", expanded=bool(narrative_base)):
            plan["narrative"] = st.text_area("Conceptual framework narrative", narrative_base,
                                             key=f"m2_narrative_{v}", label_visibility="collapsed",
                                             placeholder="A few sentences on how your constructs relate and why.")
    _add_construct_here(lib, plan, construct_labels, construct_names, v, narrative_base)

    # ------------------------------------------------------------ Step 6
    st.subheader("Step 6 · Review, save, and continue")
    issues = P.problems(lib, plan)
    for issue in issues:
        st.error(issue)
    empty = not plan["constructs"] and not plan["standard_variables"] and not plan["external_variables"]
    measured = len({m["construct"] for m in measures})
    st.markdown(f"**Your plan:** {len(constructs)} construct(s), {measured} with a measure; "
                f"{len(plan['standard_variables']) + len(plan['external_variables'])} other variable(s)"
                + (f"; timepoints {', '.join(plan['timepoints'])}" if plan["timepoints"] else "") + ".")
    book = None
    if not issues and (plan["constructs"] or plan["standard_variables"] or plan["external_variables"]):
        book = P.build_codebook(lib, plan)
        if plan["measures"]:
            with st.expander("Alignment: construct → measure → variables"):
                st.dataframe(pd.DataFrame(P.alignment(lib, plan)), use_container_width=True, hide_index=True)
        with st.expander(f"Codebook: {len(book)} variables"
                         + (f", {len(book.constructs)} construct(s) without a measure yet" if book.constructs else "")):
            st.caption("**metadata_code** is the same in every study that uses the same construct, measure, item, "
                       "and target (Construct_Measure_Item_Target), so studies can be matched at each level. "
                       "**name** is the column name in your data file.")
            st.dataframe(pd.DataFrame(book.to_rows())[["name", "metadata_code", "code_level", "label", "data_type",
                                                       "values", "question", "construct_ids", "notes"]],
                         use_container_width=True, hide_index=True)
        manifest = P.manifest(lib, plan)
        st.session_state["module2_variable_manifest"] = manifest
        st.download_button("Download codebook (CSV)", book.to_csv().encode("utf-8"), file_name="codebook.csv",
                           mime="text/csv", key="m2_dl_cb_csv")
        with st.expander("More downloads"):
            d1, d2, d3 = st.columns(3)
            d1.download_button("Codebook (JSON)", book.to_json().encode("utf-8"), file_name="codebook.json",
                               mime="application/json", key="m2_dl_cb_json", use_container_width=True)
            d2.download_button("Variable matrix for Module 5 (CSV)", pd.DataFrame(manifest).to_csv(index=False).encode("utf-8"),
                               file_name="variable_matrix.csv", mime="text/csv", key="m2_dl_manifest", use_container_width=True)
            d3.download_button("Diagram (Graphviz DOT)", P.diagram_dot(lib, plan).encode("utf-8"),
                               file_name="framework_diagram.dot", mime="text/vnd.graphviz", key="m2_dl_dot",
                               use_container_width=True)
    st.caption("**Saving moves your work into Module 3:** your framework and constructs are added to your study "
               "profile, and your variables are used in Module 3's DDI export. You can come back and add more later.")
    dois = P.published_dois(plan)
    add_dois = False
    if dois and record is not None:
        new = [d for d in dois if d["doi"].lower() not in {(r.get("identifier") or "").lower()
                                                            for r in record["resource"].get("related") or []}]
        if new:
            add_dois = st.checkbox(
                f"Also list the published instrument(s) you use in your study profile ({len(new)}): "
                + "; ".join(f"{d['name']} (doi:{d['doi']})" for d in new),
                value=True, key=f"m2_add_dois_{v}",
                help="Adds each DOI to the study profile's related works (cited by the study), so your study "
                     "record and its DataCite metadata name the instrument even though it is not in the library.")
    if st.button("Save variable plan and continue", type="primary", disabled=bool(issues) or empty, key="m2_save"):
        project = current_project()
        project["module2_plan"] = plan
        st.session_state["project"] = project
        st.session_state["m2_marker"] = _project_plan_marker(project)
        added = 0
        if record is not None:
            record["study"]["design"]["frameworks"] = list(plan["frameworks"])
            if plan["framework_description"].strip():
                record["study"]["design"]["framework_description"] = plan["framework_description"].strip()
            record["study"]["constructs"], added = P.merge_profile_constructs(record["study"].get("constructs"), plan)
            if add_dois:
                record["resource"]["related"], dois_added = P.merge_related_dois(record["resource"].get("related"), plan)
                st.session_state["m2_saved_dois"] = dois_added
            store_record(record, reset_widgets=True)
        st.session_state["m2_saved"] = added
        _rebase(plan)
    if empty:
        st.caption("Add at least one construct (Step 2) or variable (Step 4) to save.")
    elif issues:
        st.caption("Fix the items listed above to save.")
    _next_step(lib)

    st.session_state["m2_pending"] = plan
    _share(lib, plan, book, publish_disabled, publish_hint)


NEW_CONSTRUCT = "New construct: "


def _search_library(lib, constructs: list[dict], construct_display: dict, construct_from_key: dict,
                    v: int) -> tuple[list[dict], list[dict]]:
    """Search box for library instruments. Returns the measures ticked and any constructs they add."""
    query = st.text_input("Search the library for an instrument", key=f"m2_inst_q_{v}",
                          placeholder="Name, acronym, author, or what it measures, e.g. belonging, MSLQ, Libarkin")
    if not query.strip():
        return [], []
    hits = P.search_instruments(lib, query)
    if not hits:
        st.caption("Nothing in the library matches. If it is a published instrument, add it under **A published "
                   "instrument that is not in the library** below.")
        return [], []
    by_shared = {}
    for c in constructs:
        by_shared.setdefault(c.get("shared_construct_id"), c["id"])
    new_options = {}
    for h in hits:
        for sid in h["construct_ids"]:
            if sid not in by_shared:
                new_options[NEW_CONSTRUCT + lib.constructs[sid]["label"]] = sid

    def default(h):
        mine = next((by_shared[s] for s in h["construct_ids"] if s in by_shared), None)
        if mine:
            return construct_from_key.get(mine)
        return NEW_CONSTRUCT + lib.constructs[h["construct_ids"][0]]["label"] if h["construct_ids"] else None

    st.caption(f"{len(hits)} match(es). Tick **Add** and choose which of your constructs it measures; "
               "\"New construct\" adds that shared construct to your plan too.")
    df = st.data_editor(
        pd.DataFrame([{"Add": False, "Instrument": h["instrument"], "Part": h["part"],
                       "Developed to measure": ", ".join(h["measures"]), "For your construct": default(h)}
                      for h in hits]),
        disabled=["Instrument", "Part", "Developed to measure"], hide_index=True, use_container_width=True,
        key=f"m2_inst_hits_{v}",
        column_config={"Add": st.column_config.CheckboxColumn("Add"),
                       "For your construct": st.column_config.SelectboxColumn(
                           "For your construct", options=[*construct_display, *sorted(new_options)])})
    picks, added, unassigned = [], {}, 0
    keys = {c["id"] for c in constructs}
    for h, row in zip(hits, df.to_dict(orient="records")):
        if row.get("Add") is not True:
            continue
        target = _s(row.get("For your construct"))
        if target in new_options:
            new = P.shared_list_construct(lib, new_options[target])
            if new["id"] not in keys:
                added.setdefault(new["id"], new)
            cid = new["id"]
        else:
            cid = construct_display.get(target)
        if not cid:
            unassigned += 1
            continue
        picks.append(P.as_measure({"construct": cid, "kind": "instrument", "instrument_id": h["instrument_id"],
                                   "version_id": h["version_id"], "dimension_id": h["dimension_id"]}))
    if unassigned:
        st.caption(f"Choose a construct for {unassigned} ticked row(s).")
    return picks, list(added.values())


def _published_instruments(published_base: list[dict], construct_display: dict, construct_from_key: dict,
                           constructs: list[dict], v: int) -> list[dict]:
    """Published instruments that are not in the library: name, first author and year, DOI."""
    with st.expander(f"Published instruments not in the library ({len(published_base)})" if published_base
                     else "A published instrument that is not in the library", expanded=bool(published_base)):
        st.caption("Give its name, the first author and year of its original publication, and its DOI (the "
                   "instrument's own record if it has one, otherwise the paper that published it). Studies that use "
                   "the same instrument are matched by its DOI, and its metadata code uses the author and year, as for "
                   "library instruments (e.g. Smith2017).")
        df = st.data_editor(
            pd.DataFrame([{"Construct": construct_from_key.get(m.get("construct")), "Instrument name": m.get("label") or "",
                           "First author and year": m.get("citation") or "", "DOI": m.get("doi") or "",
                           "Target (optional)": m.get("target") or "", "Variable name (optional)": m.get("name") or ""}
                          for m in published_base],
                         columns=["Construct", "Instrument name", "First author and year", "DOI", "Target (optional)",
                                  "Variable name (optional)"]),
            num_rows="dynamic", use_container_width=True, key=f"m2_published_{v}",
            column_config={
                "Construct": st.column_config.SelectboxColumn("Construct", options=list(construct_display)),
                "First author and year": st.column_config.TextColumn("First author and year",
                                                                     help="For example: Smith 2017"),
                "DOI": st.column_config.TextColumn("DOI", help="For example: 10.1037/a0026659"),
            })
    out, skipped, not_dois = [], 0, []
    for row in df.to_dict(orient="records"):
        if not any(_s(x) for x in row.values()):
            continue
        cid = construct_display.get(_s(row.get("Construct")))
        name, cite, doi = _s(row.get("Instrument name")), _s(row.get("First author and year")), _s(row.get("DOI"))
        if doi and not P.normalize_doi(doi):
            not_dois.append(doi)
        if not cid or not name or not (metacode.author_year(cite) or P.normalize_doi(doi)):
            skipped += 1
            continue
        out.append(P.published_measure(cid, name, cite, doi, _s(row.get("Target (optional)")),
                                       _s(row.get("Variable name (optional)"))))
    st.session_state["m2_published_skipped"] = skipped
    if not_dois:
        st.warning("Not a DOI: " + ", ".join(not_dois) + ". A DOI starts with 10., for example 10.1037/a0026659.")
    if out:
        labels = {m["label"]: m for m in out}
        c1, c2 = st.columns([2, 1])
        chosen = c1.selectbox("Help others find it: recommend it for the library", list(labels),
                              key=f"m2_published_rec_{v}")
        if c2.button("Fill in a recommendation", key=f"m2_published_rec_btn_{v}", use_container_width=True):
            m = labels[chosen]
            label = next((c["label"] for c in constructs if c["id"] == m["construct"]), "")
            st.session_state.update({"m2_suggest_kind": "instrument", "m2_rec_name": m["label"],
                                     "m2_rec_citation": m["citation"], "m2_rec_doi": m["doi"],
                                     "m2_rec_construct_prefill": label})
            st.success(f"The instrument recommendation form is filled in. Open the **{TABS[1]}** tab at the top of "
                       "this page, add the full citation and what it measures, and submit.")
    return out


def _diagram_editor(plan: dict, positions: dict, names: dict, v: int):
    """Step 5's drag-and-drop diagram. Returns (arrows, box positions), or None if the component is missing."""
    try:
        from streamlit_flow import streamlit_flow
        from streamlit_flow.elements import StreamlitFlowEdge, StreamlitFlowNode
        from streamlit_flow.state import StreamlitFlowState
    except ImportError:
        return None
    keys = [c["id"] for c in plan["constructs"]]
    arrows = P.diagram_arrows(plan)
    # A new diagram whenever constructs or arrows change outside it (table edits, Step 2); moves keep the same one.
    key = f"m2_flow_{v}_{abs(hash((tuple(keys), tuple((a['id'], a['label']) for a in arrows)))) % 10**8}"
    head = {"type": "arrowclosed", "width": 22, "height": 22, "color": "#333333"}  # large, so direction is clear
    # The diagram's state is kept under its own name: Streamlit stores the component's raw value under `key`.
    state_key = f"{key}_state"
    if state_key not in st.session_state:
        st.session_state[state_key] = StreamlitFlowState(
            nodes=[StreamlitFlowNode(id=k, pos=tuple(positions[k]), data={"content": names.get(k, k)},
                                     node_type="default", source_position="right", target_position="left",
                                     draggable=True, connectable=True, selectable=True, deletable=False)
                   for k in keys],
            edges=[StreamlitFlowEdge(id=a["id"], source=a["source"], target=a["target"], marker_end=head,
                                     marker_start=head if a["both"] else {}, label=a["label"],
                                     label_show_bg=True, label_bg_style={"fill": "#ffffff", "fillOpacity": 0.95},
                                     style={"strokeWidth": 2, "stroke": "#333333"}, deletable=True, focusable=True)
                   for a in arrows])
    # Tall enough for the whole diagram, and zoom out far enough that a big one still fits.
    state = streamlit_flow(key, st.session_state[state_key], height=P.diagram_height(positions), fit_view=True,
                           min_zoom=0.2, allow_new_edges=True, enable_edge_menu=True, show_controls=True,
                           hide_watermark=True)
    st.session_state[state_key] = state
    moved = {n.id: [float(n.position["x"]), float(n.position["y"])] for n in state.nodes if n.id in positions}
    edges = P.edges_from_diagram([(e.id, e.source, e.target) for e in state.edges
                                  if e.source in positions and e.target in positions])
    return edges, {**positions, **moved}


def _add_construct_here(lib, plan: dict, construct_labels: dict, construct_names: dict, v: int, narrative: str) -> None:
    """Step 5: add a construct you realize is missing while building the diagram."""
    with st.expander("Missing something? Add a construct"):
        st.caption("Add a construct here and it joins your plan (Step 2) and the diagram. Choose it from the shared "
                   "list, or name your own.")
        c1, c2 = st.columns(2)
        name = c1.text_input("Your name for it", key=f"m2_addc_name_{v}", placeholder="e.g. Career interests")
        shared = c2.selectbox("Shared construct (optional)", [""] + list(construct_labels), key=f"m2_addc_shared_{v}",
                              help="Choose one only if it means the same thing as your construct.")
        if st.button("Add construct", key=f"m2_addc_go_{v}", disabled=not (name.strip() or shared)):
            sid = construct_labels.get(shared)
            new = (P.shared_list_construct(lib, sid) if sid and not name.strip() else
                   {"id": P.construct_key(None, name.strip()), "label": name.strip(), "framework_id": None,
                    "shared_construct_id": sid, "definition": ""})
            if new["id"] in {c["id"] for c in plan["constructs"]}:
                st.warning(f"{new['label']} is already in your plan.")
            else:
                _rebase({**plan, "constructs": plan["constructs"] + [new], "narrative": narrative})


def _icpsr_variables(base: dict, v: int) -> list[dict]:
    """Step 4: variables other studies have used, found in ICPSR's variables database and linked to it."""
    existing = base.get("external_variables") or []
    with st.expander(f"Variables from ICPSR ({len(existing)})" if existing else "Add other variables from ICPSR",
                     expanded=bool(existing)):
        st.caption("Need a variable that isn't listed above? Find how other studies asked it in ICPSR's variables "
                   "database, which documents millions of variables from social science studies. Open the variable, "
                   "copy its page address, and paste it here with the name you will use in your data. The question "
                   "wording and codes stay documented at ICPSR, and your codebook links to them.")
        st.link_button("Search ICPSR's variables database", P.ICPSR_VARIABLE_SEARCH)
        types = {label: kind for kind, label in P.EXTERNAL_TYPES.items()}
        table = st.data_editor(
            pd.DataFrame([{"ICPSR variable page": x.get("source_url"), "Variable name": x.get("name"),
                           "Label": x.get("label"), "Question text (optional)": x.get("question"),
                           "Type": P.EXTERNAL_TYPES.get(x.get("data_type"))} for x in existing],
                         columns=["ICPSR variable page", "Variable name", "Label", "Question text (optional)", "Type"]),
            num_rows="dynamic", use_container_width=True, key=f"m2_icpsr_{v}",
            column_config={
                "ICPSR variable page": st.column_config.LinkColumn(
                    "ICPSR variable page", help="The address of the variable's page at ICPSR, e.g. "
                    "https://www.icpsr.umich.edu/web/ICPSR/studies/…/datasets/1/variables/V21"),
                "Variable name": st.column_config.TextColumn(
                    "Variable name", help="The column name in your data: lowercase letters, numbers and _."),
                "Type": st.column_config.SelectboxColumn("Type", options=list(types)),
            })
    out, unfinished = [], 0
    for row in table.to_dict(orient="records"):
        url, name = _s(row.get("ICPSR variable page")), _s(row.get("Variable name"))
        if not any(_s(x) for x in row.values()):
            continue
        if not name or not P.icpsr_variable(url):
            unfinished += 1
            continue
        out.append(P.external_variable(name, _s(row.get("Label")), url, _s(row.get("Question text (optional)")),
                                       types.get(_s(row.get("Type")), "categorical")))
    if unfinished:
        st.caption(f"{unfinished} unfinished row(s) are left out until they have an ICPSR variable page address "
                   "and a variable name.")
    st.caption(f"Something every study should share? Suggest it for the library in the **{TABS[1]}** tab.")
    return out


def _next_step(lib) -> None:
    """After saving: what moved into Module 3, and the way there."""
    saved = current_project().get("module2_plan")
    if not saved:
        return
    record = current_record()
    with st.container(border=True):
        st.markdown("**Next: 3. Check, Register & Export**")
        if "m2_saved" in st.session_state:
            added = st.session_state.pop("m2_saved")
            if record is not None:
                dois_added = st.session_state.pop("m2_saved_dois", 0)
                listed = (["your framework"] if (saved.get("frameworks")) else []) + (
                    [f"{added} new construct(s)"] if added else []) + (
                    [f"{dois_added} published instrument DOI(s) as related works"] if dois_added else [])
                st.success("Variable plan saved." + (f" Your study profile now lists {' and '.join(listed)} from this plan."
                                                     if listed else ""))
            else:
                st.success("Variable plan saved to your project.")
        if record is None:
            st.warning("Your plan is saved, but there is no study profile yet, so nothing could be added to one. "
                       "Save a study profile in Module 1, then come back here and save the plan again.")
            st.button("Go to 1. Describe Your Study", key="m2_to_m1", on_click=navigate_to_module,
                      args=("1. Describe Your Study",), use_container_width=True)
        else:
            st.caption("In Module 3 you check the full study profile, register the study for a DOI, and export its "
                       "metadata. Module 3 uses the plan as last saved: if you change anything above, save again.")
            st.button("Continue to 3. Check, Register & Export →", type="primary", key="m2_to_m3",
                      on_click=navigate_to_module, args=("3. Check, Register & Export",), use_container_width=True)
        render_project_download(key="m2_project_download", label="Download project file (to keep your work)")


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
    st.caption("Your name from sign-in appears on the submission. Theory, instrument, and correction recommendations "
               "open as pull requests in the [HuMeta Instrument Library](https://github.com/JLib271/humeta-library), "
               "and analysis recommendations in the [portal's repository](https://github.com/JLib271/HuMeta). A "
               "maintainer checks the source before adding anything.")


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
        name = c1.text_input("Instrument name *", key="m2_rec_name")
        acronym = c2.text_input("Acronym")
        relationship = c3.selectbox("Your relationship to it *", list(R.RELATIONSHIPS), format_func=R.RELATIONSHIPS.get)
        c1, c2 = st.columns(2)
        citation = c1.text_area("Primary citation *", height=90, key="m2_rec_citation")
        doi = c2.text_input("DOI (optional)", placeholder="10.xxxx/xxxxx", key="m2_rec_doi")
        url = c2.text_input("Link to the instrument or its manual (optional)")
        st.markdown("**What does each part measure?** \\* One row for the whole instrument, or one row per subscale.")
        alignment_df = st.data_editor(
            pd.DataFrame([{"Part (whole instrument or subscale)": "Whole instrument", "Items (numbers or count)": "",
                           "Measures (shared construct)": None, "Or a construct not on the list": "",
                           "Theory construct (optional, e.g., SDT: Competence)": ""}]),
            num_rows="dynamic", use_container_width=True, key="m2_rec_inst_alignment",
            column_config={"Measures (shared construct)": st.column_config.SelectboxColumn(
                "Measures (shared construct)", options=list(construct_labels))})
        options = ["", *plan_constructs]
        prefill = st.session_state.pop("m2_rec_construct_prefill", None)
        if st.session_state.get("m2_rec_construct") not in options:
            st.session_state.pop("m2_rec_construct", None)
        if prefill in options:
            st.session_state["m2_rec_construct"] = prefill
        construct = st.selectbox("Construct in your plan that it measures (optional)", options, key="m2_rec_construct")
        c1, c2, c3 = st.columns(3)
        respondents = c1.text_input("Who responds?", placeholder="e.g., undergraduate students")
        item_count = c2.text_input("Total number of items")
        response_format = c3.text_input("Response format", placeholder="e.g., 5-point agreement")
        populations = st.text_input("Populations or settings it has been validated with")
        c1, c2 = st.columns(2)
        access = c1.selectbox("How can researchers get it? *", list(R.ACCESS_OPTIONS), format_func=R.ACCESS_OPTIONS.get)
        access_details = c2.text_input("License or terms of use (if known)")
        evidence = st.text_area("Reliability and validity evidence, with citations (optional)")
        c1, c2 = st.columns(2)
        development = c1.selectbox("How was it developed?", list(R.DEVELOPMENT_OPTIONS), format_func=R.DEVELOPMENT_OPTIONS.get,
                                   help="A theory is not required. Many instruments are built from a clear definition of what "
                                        "to measure.")
        theory = c2.text_input("Theory or framework it was built on (optional)")
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
            relationship=relationship, item_text_permission=permission, construct=construct, notes=notes,
            development=development, theory=theory)
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
