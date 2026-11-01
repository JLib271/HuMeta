# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 3: Check & Export Metadata.

Add the constructs measured (suggested from the Module 2 plan), check the
STEMEd+ record against the profile's rules, and export STEMEd+ JSON, DataCite
4.7 JSON/XML, and ERIC descriptors. Logic lives in oem/profile.py.
"""

from __future__ import annotations

import json
import re

import pandas as pd
import streamlit as st

from oem import profile
from oem.app.common import current_project, navigate_to_module
from oem.app.profile_form import SPEC_URL, current_record, library, show_issues, store_record


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    st.header("3. Check & Export Metadata")
    p = profile.load()
    lib = library()
    st.caption(
        f"Complete your [STEMEd+]({SPEC_URL}) record with the constructs you measure, check it against the "
        "profile's responsible-sharing rules, and export metadata that DataCite (DOIs) and ERIC understand."
    )
    record = current_record()
    if record is None:
        st.info("Start with your study profile in Module 1.")
        st.button("Go to 1. Study Metadata Profile", key="m3_to_m1", on_click=navigate_to_module,
                  args=("1. Study Metadata Profile",))
        return

    construct_labels = {c["label"]: cid for cid, c in lib.constructs.items()}
    construct_names = {cid: label for label, cid in construct_labels.items()}
    instrument_labels = {i["name"]: iid for iid, i in lib.instruments.items()}
    instrument_names = {iid: label for label, iid in instrument_labels.items()}

    st.subheader("Constructs measured")
    plan = current_project().get("module2_plan") or {}
    suggestions = [c for c in profile.suggest_constructs(lib, plan)
                   if c not in {x["construct_id"] for x in record["stemed"]["constructs"]}]
    if suggestions:
        st.caption("From your Module 2 plan: " + ", ".join(construct_names[c] for c in suggestions))
        if st.button("Add these constructs", key="m3_add_suggestions"):
            record["stemed"]["constructs"] += [{"construct_id": c, "instrument_id": None, "version_id": None,
                                                "dimension_id": None} for c in suggestions]
            store_record(record, reset_widgets=True)
            st.rerun()
    elif not plan:
        st.caption("Plan variables in Module 2 to get construct suggestions, or pick constructs below.")

    v = st.session_state.get("stemed_form_version", 0)
    with st.form(key=f"m3_constructs_{v}"):
        table = st.data_editor(
            pd.DataFrame(
                [{"construct": construct_names.get(c["construct_id"]), "instrument": instrument_names.get(c.get("instrument_id"))}
                 for c in record["stemed"]["constructs"]] or [{"construct": None, "instrument": None}],
                columns=["construct", "instrument"]),
            num_rows="dynamic", use_container_width=True, key=f"m3_constructs_table_{v}",
            column_config={
                "construct": st.column_config.SelectboxColumn("Construct", options=sorted(construct_labels)),
                "instrument": st.column_config.SelectboxColumn("Instrument from the library (optional)",
                                                               options=sorted(instrument_labels)),
            },
        )
        if st.form_submit_button("Save constructs", type="primary"):
            constructs = []
            for row in table.to_dict(orient="records"):
                cid = construct_labels.get(row.get("construct"))
                if cid and all(c["construct_id"] != cid for c in constructs):
                    constructs.append({"construct_id": cid, "instrument_id": instrument_labels.get(row.get("instrument")),
                                       "version_id": None, "dimension_id": None})
            record["stemed"]["constructs"] = constructs
            store_record(record)
            st.success("Constructs saved to your project.")

    st.subheader("Profile check")
    issues = profile.validate(record, lib, p)
    show_issues(issues)
    st.button("Edit the study profile in Module 1", key="m3_edit_m1", on_click=navigate_to_module,
              args=("1. Study Metadata Profile",))

    st.subheader("Export")
    slug = re.sub(r"[^a-z0-9]+", "-", (record["resource"].get("title") or "record").lower()).strip("-")[:50] or "record"
    st.download_button("STEMEd+ record (JSON)", json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8"),
                       file_name=f"{slug}.stemed-ap.json", mime="application/json", key="m3_dl_record",
                       use_container_width=True)
    if any(i.severity == "error" for i in issues):
        st.info("Fix the items above to enable the DataCite and ERIC exports.")
        return
    datacite = profile.to_datacite_json(record, lib, p)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("DataCite 4.7 metadata (JSON)", json.dumps(datacite, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name=f"{slug}.datacite.json", mime="application/json", key="m3_dl_dcjson",
                           use_container_width=True,
                           help="DataCite REST API 'attributes'. Without a DOI, use it to register one through your repository or DataCite member.")
    with c2:
        if (record["resource"].get("identifier") or {}).get("type") == "DOI":
            st.download_button("DataCite 4.7 metadata (XML)", profile.to_datacite_xml(record, lib, p).encode("utf-8"),
                               file_name=f"{slug}.datacite.xml", mime="application/xml", key="m3_dl_dcxml",
                               use_container_width=True)
        else:
            st.button("DataCite 4.7 metadata (XML)", disabled=True, use_container_width=True, key="m3_dl_dcxml_off",
                      help="DataCite XML requires a DOI. Add it in Module 1 once assigned.")
    descriptors = profile.eric_descriptors(record, lib, p)
    pending = [d for d in profile.eric_descriptors(record, lib, p, include_unverified=True) if d not in descriptors]
    st.markdown("**ERIC Thesaurus descriptors** (for ERIC submissions and education indexes)")
    st.code("; ".join(descriptors) or "No descriptors yet: add constructs, levels, settings, or designs.", language=None)
    st.download_button("ERIC descriptors (text)", "\n".join(descriptors).encode("utf-8"),
                       file_name=f"{slug}.eric-descriptors.txt", mime="text/plain", key="m3_dl_eric",
                       use_container_width=True)
    if pending:
        st.caption("Not yet verified against the current ERIC Thesaurus, so not included: " + "; ".join(pending))
    with st.expander("Preview DataCite JSON"):
        st.json(datacite, expanded=False)
