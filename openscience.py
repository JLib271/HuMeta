# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""HuMeta Portal: Streamlit entry point.

Run with ``streamlit run openscience.py``. Page code lives in ``oem/app/pages/``;
shared helpers in ``oem/app/common.py``; Streamlit-free logic in ``oem/``.
"""

from __future__ import annotations
import streamlit as st
import json
from oem.app.common import (auth_is_configured, render_feedback_box, current_project, empty_project, navigate_to_module, parse_project_file, render_project_download, render_value_card, researcher_display_name, researcher_is_signed_in, value_propositions)
from oem.app.pages import (
    analytics,
    data_repository,
    framework_measures,
    metadata_check,
    published_viewer,
    study_profile,
)


# Storage model (no database):
# - Private study profiles and variable plans live only in a project file the
#   researcher downloads and re-opens; the app never stores them.
# - Private datasets are analyzed in memory for the current session only.
# - Public study summaries and datasets live in this GitHub repository under
#   published/. Researchers submit them as pull requests; they become public
#   only after a maintainer merges, and the deployed app reads them from disk.

# App configuration and session setup
st.set_page_config(page_title="HuMeta Portal", layout="wide")
if "session_instruments" not in st.session_state:
    st.session_state.session_instruments = []

# Engine selection sidebar routing
st.sidebar.header("⚙️ Core Controls")
app_mode = st.sidebar.radio(
    "Navigate Workspace Module:",
    [
        "About this app",
        "1. Study Metadata Profile",
        "2. Framework and Measures",
        "3. Check & Export Metadata",
        "4. Community Data Repository Sync",
        "5. Descriptive & Scale Analytics",
        "6. Published Repository Viewer",
    ],
    key="app_mode"
)

signed_in = researcher_is_signed_in()

with st.sidebar:
    st.divider()
    st.subheader("📁 Project file")
    st.caption(
        "Your study profile (Module 1) and variable plan (Module 2) are kept in a project "
        "file on your own computer. The app does not store them. You can choose to share "
        "parts of your work: a limited study summary or a theory and variable suggestion "
        "(Module 2), or a de-identified dataset (Module 4). Shared items go to the project's "
        "GitHub repository and are reviewed before they are listed in the app."
    )
    project_upload = st.file_uploader(
        "Open a project file",
        type=["json"],
        key="project_file_upload",
        help="Open a .humeta-project.json file you downloaded earlier.",
    )
    if project_upload is not None:
        upload_marker = (project_upload.name, project_upload.size)
        if st.session_state.get("loaded_project_marker") != upload_marker:
            try:
                st.session_state["project"] = parse_project_file(project_upload.getvalue())
                st.session_state["loaded_project_marker"] = upload_marker
                st.success("Project opened.")
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as project_error:
                st.error(f"Could not open the project file: {project_error}")
    sidebar_project = current_project()
    if sidebar_project.get("study") or sidebar_project.get("module2_plan"):
        sidebar_study = sidebar_project.get("study") or {}
        st.caption(f"Current study: **{sidebar_study.get('study_title') or 'Untitled draft'}**")
        render_project_download(key="sidebar_project_download")
        if st.button("Start a new project", use_container_width=True):
            st.session_state["project"] = empty_project()
            st.session_state.pop("loaded_project_marker", None)
            st.rerun()
    else:
        st.caption("No study profile yet. Save one in Module 1, or open a project file.")

    st.divider()
    st.subheader("🔐 Researcher sign-in")
    if not auth_is_configured():
        st.caption(
            "Sign-in is not configured for this deployment. Everything works without it "
            "except submitting items for public listing."
        )
    elif signed_in:
        st.caption(f"Signed in as {researcher_display_name()}")
        if st.button("Sign out", use_container_width=True):
            st.logout()
    else:
        st.caption(
            "Sign in with a Google account (including university Google accounts) to submit study summaries, "
            "public datasets, or suggestions for review."
        )
        if st.button("Sign in with Google", use_container_width=True, type="primary"):
            st.login()

    st.divider()
    st.caption("💬 Trying the app? Use **Send feedback about this page** at the bottom of any page. "
               "No GitHub account needed.")

    # AGPL-3.0 section 13: offer users of the hosted app its source code.
    st.divider()
    st.caption(
        "Free software under the [GNU AGPL v3](https://www.gnu.org/licenses/agpl-3.0.html). "
        "[Source code](https://github.com/JLib271/HuMeta)"
    )

st.title("🔬 HuMeta Portal")
st.caption("Built on HuMeta: The Social Science, Humanities, and Education Study Metadata Profile")
st.caption("Study metadata aligned with DataCite, Dublin Core, DDI, schema.org, and ERIC, with an open instrument library.")

if app_mode == "About this app":
    st.header("🔬 Accelerating Research in Education, the Social Sciences, and the Humanities")
    st.markdown(
        "This platform is specifically engineered to resolve the most critical bottlenecks in "
        "research across education, the social sciences, the humanities, and related fields by "
        "enforcing data structural integrity and empowering open-science collaboration."
    )
    for value_card in value_propositions:
        render_value_card(value_card, show_open_button=True)
else:
    st.button(
        "← About this app",
        key="back_to_about",
        on_click=navigate_to_module,
        args=("About this app",)
    )
    active_card = next(card for card in value_propositions if card[3] == app_mode)
    render_value_card(active_card)

st.markdown("---")

# Nothing private is stored by the app, so every module is fully usable without
# signing in. Sign-in is required only to submit items for public review.
publish_disabled = not signed_in
publish_hint = (
    None if signed_in
    else "Sign in with Google (sidebar) to submit this for maintainer review."
)

PAGES = {
    "1. Study Metadata Profile": study_profile.render,
    "2. Framework and Measures": framework_measures.render,
    "3. Check & Export Metadata": metadata_check.render,
    "4. Community Data Repository Sync": data_repository.render,
    "5. Descriptive & Scale Analytics": analytics.render,
    "6. Published Repository Viewer": published_viewer.render,
}

if app_mode in PAGES:
    PAGES[app_mode](signed_in=signed_in, publish_disabled=publish_disabled, publish_hint=publish_hint)

render_feedback_box(app_mode)
