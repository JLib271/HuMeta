# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 6: Find Related Data.

Datasets deposited in the STEMEd+ Library that share instruments, constructs,
or theories with your study, from the index the HuMeta Library website
publishes daily; plus the study summaries researchers have shared.
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from oem import datasets as D
from oem.app.common import load_published_summaries, navigate_to_module
from oem.app.profile_form import current_record, library


@st.cache_data(ttl=3600, show_spinner=False)
def _dataset_index() -> dict | None:
    if os.environ.get("HUMETA_LIBRARY_SNAPSHOT"):  # the tests: no network
        return {"format": "humeta-dataset-index", "datasets": []}
    try:
        return D.fetch_index()
    except Exception:  # noqa: BLE001 - shown as "can't reach the Library" below
        return None


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    st.header("🔎 Find Related Data")
    st.caption(
        "Datasets in the [STEMEd+ Library](" + D.DATA_COLLECTION_URL + ") that used the same instruments, constructs, or "
        "theories as your study. The data stay in the STEMEd+ Library; follow a link to see each deposit and its terms."
    )
    tab_related, tab_all, tab_summaries = st.tabs(["Related to my study", "All datasets", "Shared study summaries"])
    index = _dataset_index()

    with tab_related:
        record = current_record()
        if index is None:
            st.warning("Can't reach the HuMeta Library's dataset list right now. Try again later, or "
                       f"[browse the datasets]({D.DATASETS_PAGE_URL}) directly.")
        elif record is None:
            st.info("Describe your study in Module 1 and add the constructs and instruments you used (Module 3) to find "
                    "related datasets.")
            st.button("Go to 1. Study Metadata Profile", key="m6_to_m1", on_click=navigate_to_module,
                      args=("1. Study Metadata Profile",))
        else:
            links = D.study_links(record)
            if not (links["instruments"] or links["constructs"] or links["frameworks"]):
                st.info("Your profile doesn't name instruments, constructs, or theories yet. Add them in Module 3 to find "
                        "related datasets.")
                st.button("Go to 3. Check & Export Metadata", key="m6_to_m3", on_click=navigate_to_module,
                          args=("3. Check & Export Metadata",))
            else:
                matches = D.related(index, record)
                if not matches:
                    st.info("No deposited datasets share an instrument, construct, or theory with your study yet. Yours "
                            "could be the first: see Module 4.")
                for m in matches:
                    _dataset_card(m.dataset, "Shares " + ", ".join(m.reasons))

    with tab_all:
        if index is None:
            st.warning(f"Can't reach the dataset list right now. [Browse the datasets]({D.DATASETS_PAGE_URL}) directly.")
        else:
            rows = index.get("datasets") or []
            if not rows:
                st.info("No datasets have been deposited in the STEMEd+ Library's Data collection yet.")
            else:
                lib = library()
                st.dataframe(pd.DataFrame([{
                    "Title": d.get("title"), "Creators": ", ".join(d.get("creators") or []),
                    "Published": d.get("date"),
                    "Instruments": ", ".join((lib.instruments.get(i) or {}).get("name", i) for i in d.get("instruments") or []),
                    "Page": D.dataset_page(d),
                } for d in rows]), use_container_width=True, hide_index=True,
                    column_config={"Page": st.column_config.LinkColumn("HuMeta Library page", display_text="Open")})
            if index.get("fetched"):
                st.caption(f"From the STEMEd+ Library, checked {index['fetched']}.")
        st.button("How to deposit your data (Module 4)", key="m6_to_m4", on_click=navigate_to_module,
                  args=("4. Deposit Data in the STEMEd+ Library",))

    with tab_summaries:
        summaries = load_published_summaries()
        if not summaries:
            st.info("No study summaries have been shared yet. Share yours from Module 2.")
        else:
            st.dataframe(pd.DataFrame([{
                "Study": item.get("study_title", ""),
                "Content domain": (item.get("study_metadata") or {}).get("content_domain", ""),
                "Theories": ", ".join((item.get("study_metadata") or {}).get("selected_theories", []) or []),
                "Variables": len((item.get("study_metadata") or {}).get("variables", []) or []),
                "Shared": item.get("published_at", ""),
            } for item in summaries]), use_container_width=True, hide_index=True)


def _dataset_card(ds: dict, why: str) -> None:
    with st.container(border=True):
        st.markdown(f"**[{ds.get('title')}]({D.dataset_page(ds)})**")
        meta = " · ".join(x for x in (", ".join(ds.get("creators") or []), (ds.get("date") or "")[:4]) if x)
        st.caption(" · ".join(x for x in (meta, why, "files restricted" if ds.get("files_public") is False else "") if x))
        if ds.get("description"):
            st.write(ds["description"])
        st.link_button("Get the data", ds.get("url") or D.dataset_page(ds))
