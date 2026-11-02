# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 6: Published Repository Viewer."""

from __future__ import annotations
import streamlit as st
import pandas as pd
import json
from oem.app.common import (load_measure_catalog, load_published_datasets, load_published_summaries)


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    st.header("🗄️ Published Repository Viewer")
    st.caption(
        "Read-only view of everything researchers have published through reviewed pull "
        "requests: study summaries, the public dataset catalog, and the measure catalog."
    )
    st.markdown("---")

    view_options = {
        "Published study summaries": "summaries",
        "Public dataset catalog": "datasets",
        "Research measure catalog": "measures",
    }
    view_label = st.radio("Select a table", list(view_options), horizontal=True, key="active_repository_view")
    view = view_options[view_label]

    if view == "summaries":
        records = [
            {
                "study_title": item.get("study_title", ""),
                "content_domain": (item.get("study_metadata") or {}).get("content_domain", ""),
                "frameworks": ", ".join((item.get("study_metadata") or {}).get("selected_theories", []) or []),
                "unit_of_analysis": (item.get("study_metadata") or {}).get("unit_of_analysis", ""),
                "variable_count": len((item.get("study_metadata") or {}).get("variables", []) or []),
                "published_at": item.get("published_at", ""),
            }
            for item in load_published_summaries()
        ]
    elif view == "datasets":
        records = [
            {
                key: value for key, value in item.items()
                if not key.startswith("_") and key != "columns"
            }
            for item in load_published_datasets()
        ]
    else:
        try:
            records = load_measure_catalog()
        except (OSError, ValueError, json.JSONDecodeError) as catalog_error:
            records = []
            st.error(f"Could not read the measure catalog: {catalog_error}")

    display_df = pd.DataFrame(records)
    if display_df.empty:
        st.info(f"Nothing has been published in “{view_label}” yet.")
    else:
        st.dataframe(display_df.astype(str), use_container_width=True, hide_index=True)
        st.download_button(
            label=f"📥 Download {view_label} (.csv)",
            data=display_df.to_csv(index=False).encode("utf-8"),
            file_name=f"humeta_{view}.csv",
            mime="text/csv",
            use_container_width=True,
        )
