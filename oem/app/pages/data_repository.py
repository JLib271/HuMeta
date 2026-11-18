# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 4: Deposit Data in the STEMEd+ Commons Library.

Data are deposited in the STEMEd+ Commons Library's Data collection,
which gives each deposit a DOI and handles access. This module gets a
researcher ready: their HuMeta profile (humeta.json) to attach, and the HuMeta
keywords that link the deposit to the HuMeta Library. The portal itself never
receives or stores datasets.
"""

from __future__ import annotations

import json
import re

import streamlit as st

from oem import datasets as D
from oem import profile
from oem.app.common import navigate_to_module
from oem.app.common import LICENSE_HELP
from oem.app.profile_form import LICENSE_URLS, LICENSES, current_record, library, show_issues, store_record


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    st.header("📦 Deposit Data in the STEMEd+ Commons Library")
    st.caption(
        "Share your data in the [STEMEd+ Commons Library's Data collection](" + D.DATA_COLLECTION_URL + "). "
        "It gives your dataset a DOI, keeps restricted files restricted, and links it to the instruments, constructs, "
        "and theories you used, so others can find it from the [HuMeta Library](" + D.DATASETS_PAGE_URL + ")."
    )
    st.info(
        "🔒 **The portal never receives your data.** You upload your files directly to the STEMEd+ Commons Library. To analyze "
        "data you can't share, use Module 5: files are read in memory for your session only."
    )

    record = current_record()
    if record is None:
        st.subheader("1 · Describe your study first")
        st.write("Your deposit is linked through your study profile. Start it in Module 1, add the constructs and "
                 "instruments you used (Modules 2 and 3), then come back here.")
        st.button("Go to 1. Describe Your Study", key="m4_to_m1", on_click=navigate_to_module,
                  args=("1. Describe Your Study",))
        _browse_link()
        return

    lib = library()
    p = profile.load()
    links = D.study_links(record)
    keywords = D.linking_keywords(record)

    st.subheader("1 · Check your study profile")
    if not (links["instruments"] or links["constructs"] or links["frameworks"]):
        st.warning("Your profile doesn't name any instruments, constructs, or theories yet, so your deposit won't link "
                   "to the HuMeta Library. Add constructs and instruments in Module 3 (and theories in Module 2).")
        st.button("Go to 3. Check, Register & Export", key="m4_to_m3", on_click=navigate_to_module,
                  args=("3. Check, Register & Export",))
    else:
        names = {
            "instruments": lambda i: (lib.instruments.get(i) or {}).get("name", i),
            "constructs": lambda c: (lib.constructs.get(c) or {}).get("label", c),
            "frameworks": lambda f: (lib.frameworks.get(f) or {}).get("label", f),
        }
        for kind, title in (("instruments", "Instruments"), ("constructs", "Constructs"), ("frameworks", "Theories")):
            if links[kind]:
                st.markdown(f"**{title}:** " + ", ".join(names[kind](x) for x in links[kind]))
    issues = profile.validate(record, lib, p)
    if issues:
        with st.expander("Profile check"):
            show_issues(issues)
    ethics = (record.get("study") or {}).get("ethics") or {}
    if ethics.get("identifiability") in ("identifiable", "coded"):
        st.warning("Your profile says the data may identify participants. Deposit only data your consent forms, ethics "
                   "approval, and data agreements allow you to share, and restrict the files if needed.")

    st.subheader("2 · Choose a license for your data")
    _choose_license(record)

    st.subheader("3 · Download your HuMeta profile")
    st.write("Attach this file to your deposit, named **humeta.json**. It describes your study in detail, so the HuMeta "
             "Library can link your dataset precisely. If you will restrict your files, it still helps you, but the "
             "keywords in step 5 are what link the deposit.")
    st.download_button("Download humeta.json", json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8"),
                       file_name="humeta.json", mime="application/json", type="primary", key="m4_dl_humeta",
                       use_container_width=True)

    st.subheader("4 · Deposit in the STEMEd+ Commons Library")
    st.write("Sign in to the STEMEd+ Commons Library (free; Google, ORCID, GitHub, or your institution), choose **Dataset** as the "
             "resource type, upload your data files and **humeta.json**, and fill in the form.")
    st.link_button("Start a deposit in the Data collection", D.DATA_DEPOSIT_URL, use_container_width=True)
    title = (record.get("resource") or {}).get("title")
    if title:
        st.caption(f"Use the title from your profile: “{title}”.")
    identifier = (record.get("resource") or {}).get("identifier") or {}
    if identifier.get("type") == "DOI" and identifier.get("value"):
        st.write("Link the dataset to your registered study: under **Related works**, add your study's DOI.")
        st.code(identifier["value"], language=None)
    else:
        st.caption("Registering your study first (Module 3) gives it a DOI that this dataset can link back to.")

    st.subheader("5 · Add the HuMeta keywords")
    if keywords:
        st.write("In the deposit form's **Keywords** (subjects) field, add each of these exactly. They link your deposit to "
                 "the HuMeta Library, even if its files are restricted.")
        st.code("\n".join(keywords), language=None)
    else:
        st.caption("Add instruments, constructs, or theories to your profile to get HuMeta keywords.")

    st.subheader("6 · See it linked")
    st.write("Within a day, your dataset appears on the HuMeta Library's Datasets page and on the pages of the "
             "instruments, constructs, and theories it used. Module 6 shows datasets related to your study.")
    _browse_link()

    slug = re.sub(r"[^a-z0-9]+", "-", (title or "study").lower()).strip("-")[:40] or "study"
    st.download_button("Download the keywords (text)", "\n".join(keywords).encode("utf-8"),
                       file_name=f"{slug}-humeta-keywords.txt", mime="text/plain", key="m4_dl_keywords",
                       disabled=not keywords)


def _choose_license(record: dict) -> None:
    """The data license: saved in the study profile (and so in humeta.json) and chosen again in the deposit form."""
    res = record["resource"]
    current = (res.get("license") or {}).get("spdx")
    options = list(LICENSES)
    chosen = st.selectbox("Data license", options, index=options.index(current) if current in options else 0,
                          format_func=lambda k: LICENSES[k], key="m4_license",
                          help=profile.alignment_help("resource.license"))
    st.caption(LICENSE_HELP + " Choose the same license in the deposit form.")
    if chosen != current and (chosen or current):
        res["license"] = {"spdx": chosen, "name": LICENSES[chosen], "url": LICENSE_URLS.get(chosen)} if chosen else None
        store_record(record)


def _browse_link() -> None:
    st.link_button("Browse datasets in the HuMeta Library", D.DATASETS_PAGE_URL)
