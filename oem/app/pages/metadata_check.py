# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 3: Check & Export Metadata.

Add the constructs measured (suggested from the variable plan in Module 2), check the
study profile against the profile's rules, and export HuMeta JSON, DataCite
4.7 JSON/XML, and ERIC descriptors. Logic lives in oem/profile.py.
"""

from __future__ import annotations

import datetime as dt
import json
import re

import pandas as pd
import streamlit as st

from oem import datasets as D
from oem import ddi
from oem import plan as plan_model
from oem import profile
from oem import study_pdf
from oem.app.common import current_project, navigate_to_module
from oem.app.profile_form import SPEC_URL, current_record, library, show_issues, store_record


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    st.header("3. Check & Export Metadata")
    p = profile.load()
    lib = library()
    st.caption(
        f"Complete your study profile with the constructs you measure, check it against the "
        f"[HuMeta]({SPEC_URL}) responsible-sharing rules, and export metadata that DataCite (DOIs) and ERIC understand."
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
    st.caption("Choose the constructs your study measures.", help=profile.alignment_help("study.constructs"))
    plan = current_project().get("module2_plan") or {}
    suggestions = [c for c in profile.suggest_constructs(lib, plan)
                   if c not in {x["construct_id"] for x in record["study"]["constructs"]}]
    if suggestions:
        st.caption("From your variable plan (Module 2): " + ", ".join(construct_names[c] for c in suggestions))
        if st.button("Add these constructs", key="m3_add_suggestions"):
            linked = {c["construct_id"]: c for c in plan_model.profile_constructs(plan_model.normalize(plan, lib))}
            record["study"]["constructs"] += [linked.get(c) or {"construct_id": c, "instrument_id": None, "version_id": None,
                                                                "dimension_id": None} for c in suggestions]
            store_record(record, reset_widgets=True)
            st.rerun()
    elif not plan:
        st.caption("Plan variables in Module 2 to get construct suggestions, or pick constructs below.")

    v = st.session_state.get("profile_form_version", 0)
    with st.form(key=f"m3_constructs_{v}"):
        table = st.data_editor(
            pd.DataFrame(
                [{"construct": construct_names.get(c["construct_id"]), "instrument": instrument_names.get(c.get("instrument_id"))}
                 for c in record["study"]["constructs"]] or [{"construct": None, "instrument": None}],
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
            record["study"]["constructs"] = constructs
            store_record(record)
            st.success("Constructs saved to your project.")

    st.subheader("Profile check")
    issues = profile.validate(record, lib, p)
    show_issues(issues)
    st.button("Edit the study profile in Module 1", key="m3_edit_m1", on_click=navigate_to_module,
              args=("1. Study Metadata Profile",))

    st.subheader("Export")
    slug = re.sub(r"[^a-z0-9]+", "-", (record["resource"].get("title") or "record").lower()).strip("-")[:50] or "record"
    st.download_button("Study profile (HuMeta JSON)", json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8"),
                       file_name=f"{slug}.humeta.json", mime="application/json", key="m3_dl_record",
                       use_container_width=True)
    if any(i.severity == "error" for i in issues):
        st.info("Fix the items above to enable the DataCite and ERIC exports.")
        return
    _register_study(record)
    st.subheader("Other exports")
    datacite = profile.to_datacite_json(record, lib, p, "StudyRegistration")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("DataCite 4.7 metadata (JSON)", json.dumps(datacite, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name=f"{slug}.datacite.json", mime="application/json", key="m3_dl_dcjson",
                           use_container_width=True,
                           help="DataCite REST API 'attributes' for the study's registration (resource type StudyRegistration).")
    with c2:
        if (record["resource"].get("identifier") or {}).get("type") == "DOI":
            st.download_button("DataCite 4.7 metadata (XML)", profile.to_datacite_xml(record, lib, p, "StudyRegistration").encode("utf-8"),
                               file_name=f"{slug}.datacite.xml", mime="application/xml", key="m3_dl_dcxml",
                               use_container_width=True)
        else:
            st.button("DataCite 4.7 metadata (XML)", disabled=True, use_container_width=True, key="m3_dl_dcxml_off",
                      help="DataCite XML requires a DOI. Register the study above to get one.")
    plan = current_project().get("module2_plan")
    has_plan = bool((plan or {}).get("measures"))
    st.download_button("DDI-Codebook 2.5 (XML)", ddi.to_ddi_codebook_xml(record, plan if has_plan else None, lib, p).encode("utf-8"),
                       file_name=f"{slug}.ddi.xml", mime="application/xml", key="m3_dl_ddi", use_container_width=True,
                       help="DDI is the social sciences' metadata standard, used by ICPSR, CESSDA archives, the UK Data "
                            "Service, and Dataverse. This file describes the study" + (" and every variable in your Module 2 "
                            "variable plan, including the construct each one measures." if has_plan else
                            ". Save a variable plan in Module 2 to add variable-level documentation.")
                            + " Give it to your archive at deposit or keep it with your data.")
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


def _register_study(record: dict) -> None:
    """Register the study (its design) in the STEMEd+ Library's Studies collection, and save its DOI."""
    st.subheader("Register your study in the STEMEd+ Library")
    res = record["resource"]
    doi = (res.get("identifier") or {}).get("value") if (res.get("identifier") or {}).get("type") == "DOI" else None
    if doi:
        st.success(f"Your study is registered: [https://doi.org/{doi}](https://doi.org/{doi}). Datasets and other "
                   "outputs from the study link back to this DOI (Module 4 shows how).")
    else:
        st.write(
            "Give your study its own DOI by depositing this profile in the [STEMEd+ Library's Studies collection]("
            + D.STUDIES_COLLECTION_URL + ") on Knowledge Commons. The DOI stays with the study: the dataset, "
            "instruments, and papers that come from it link back to it. Deposits are public and permanent, so "
            "register when you are ready for the design to be public; you can add new versions as the study changes."
        )
    with st.expander("How to register", expanded=not doi):
        st.markdown("**1.** Download both files and attach both to the deposit: the **PDF** is the readable study "
                    "profile for people; **humeta.json** is the same profile for the HuMeta Library and other tools.")
        c1, c2 = st.columns(2)
        c1.download_button("Download the study profile (PDF)", study_pdf.study_pdf(record, library(), profile.load()),
                           file_name="study-profile.pdf", mime="application/pdf", key="m3_dl_register_pdf",
                           type="primary" if not doi else "secondary", use_container_width=True)
        c2.download_button("Download humeta.json", json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name="humeta.json", mime="application/json", key="m3_dl_register",
                           type="primary" if not doi else "secondary", use_container_width=True)
        st.markdown("**2.** Start a deposit in the Studies collection. Sign in to Knowledge Commons (free; Google, ORCID, "
                    "GitHub, or your institution).")
        st.link_button("Start a deposit in the Studies collection", D.STUDIES_DEPOSIT_URL, use_container_width=True)
        st.markdown("**3.** Copy these into the deposit form.")
        creators = "; ".join(c["name"] + (f" (ORCID {c['orcid']})" if c.get("orcid") else "")
                             for c in res.get("creators") or [])
        st.markdown("Title")
        st.code(res.get("title") or "", language=None)
        st.markdown("Creators")
        st.code(creators, language=None)
        if res.get("description"):
            st.markdown("Description")
            st.code(res["description"], language=None)
        keywords = list(dict.fromkeys([*(res.get("keywords") or []), *D.linking_keywords(record)]))
        if keywords:
            st.markdown("Keywords (add each one; the `humeta:` keywords link the study to the HuMeta Library)")
            st.code("\n".join(keywords), language=None)
        st.markdown("**4.** When Knowledge Commons gives you the DOI, paste it here and save your project.")
        c1, c2 = st.columns([3, 1])
        entered = c1.text_input("Study DOI", doi or "", key="m3_study_doi", placeholder="10.17613/...",
                                label_visibility="collapsed")
        if c2.button("Save DOI", key="m3_save_doi", use_container_width=True):
            match = re.search(r"10\.\d{4,9}/\S+", entered or "")
            if not match:
                st.error("That doesn't look like a DOI. It starts with 10. (for example 10.17613/abcd-1234).")
            else:
                res["identifier"] = {"value": match.group(0).rstrip("."), "type": "DOI"}
                res["publisher"] = res.get("publisher") or D.KC_PUBLISHER
                res["publication_year"] = res.get("publication_year") or dt.date.today().year
                store_record(record)
                st.rerun()
