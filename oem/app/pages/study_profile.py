# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 1: Study Metadata Profile.

The study is described directly with the HuMeta
Profile. Constructs are added in Module 3 after Module 2's variable plan.
"""

from __future__ import annotations

import json

import streamlit as st

from oem import profile
from oem.app.common import automate_github_pull_request, navigate_to_module, public_submission_warning, render_project_download
from oem.app.profile_form import SPEC_URL, current_record, record_form, store_record

CONSTRUCT_RULES = {"R1"}  # constructs are completed in Module 3


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    st.header("1. Study Metadata Profile")
    p = profile.load()
    st.caption(
        f"Describe your study with [HuMeta: The Social Science, Humanities, and Education Study Metadata Profile]({SPEC_URL}) (version {p.version}): "
        "the study and team, design, population and context, instructional setting, ethics and consent, and "
        "Indigenous data governance (CARE). Everything is saved to your project file; the app keeps no copy."
    )

    record = current_record()
    with st.expander("Import a saved study profile (HuMeta JSON file)", expanded=False):
        uploaded = st.file_uploader("Study profile (.humeta.json)", type=["json"], key="module1_import")
        if uploaded is not None and st.button("Use this study profile", key="module1_import_go"):
            try:
                loaded = json.loads(uploaded.getvalue().decode("utf-8"))
                if loaded.get("profile") != profile.PROFILE_ID:
                    raise ValueError("This file is not a HuMeta study profile.")
                store_record(profile.migrate(loaded, p), reset_widgets=True)
                st.rerun()
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as error:
                st.error(f"Could not import the record: {error}")

    new = record_form(record or profile.empty_record(p))
    if new is not None:
        store_record(new)
        record = new
        st.success("Study profile saved to your project. Download the project file to keep it.")

    if record is None:
        st.info("Fill in the form and save to start your study profile.")
        return

    issues = [i for i in profile.validate(record) if i.rule not in CONSTRUCT_RULES]
    errors = sum(i.severity == "error" for i in issues)
    warnings = sum(i.severity == "warning" for i in issues)
    with st.container(border=True):
        if errors or warnings:
            st.markdown(f"**Profile check:** {errors} item(s) to fix and {warnings} to review. "
                        "Details are listed in Module 3.")
        else:
            st.markdown("**Profile check:** the study profile is complete so far.")
        st.caption("Next: plan variables in Module 2, then add the constructs you measure and export the "
                   "metadata in Module 3.")
        c1, c2 = st.columns(2)
        c1.button("Go to 2. Framework and Measures", key="module1_to_m2", on_click=navigate_to_module,
                  args=("2. Framework and Measures",), use_container_width=True)
        c2.button("Go to 3. Check & Export Metadata", key="module1_to_m3", on_click=navigate_to_module,
                  args=("3. Check & Export Metadata",), use_container_width=True)
    render_project_download(key="module1_project_download")

    st.markdown("---")
    st.markdown("### Propose a change to the HuMeta profile")
    st.caption("Suggest a new element, a vocabulary term, or a clearer definition. Proposals are reviewed publicly "
               "(see GOVERNANCE.md); do not include confidential study details.")
    with st.expander("Draft a proposal"):
        public_submission_warning()
        target = st.text_input("Element or vocabulary", placeholder="e.g., learning_environment: add 'makerspace'",
                               key="module1_proposal_target")
        details = st.text_area("Proposed change and rationale", key="module1_proposal_text")
        if target and details:
            payload = (
                "**HuMeta profile change proposal**\n\n"
                f"**Profile version:** {p.version}\n\n**Element / vocabulary:** {target}\n\n"
                f"### Proposed change and rationale\n```text\n{details}\n```\n\n"
                "---\n*Submitted from HuMeta Portal Module 1.*"
            )
            if st.button("Submit proposal as a pull request", key="module1_proposal_submit",
                         disabled=publish_disabled, help=publish_hint):
                with st.spinner("Opening a pull request for review..."):
                    safe_name = "".join(ch if ch.isalnum() else "_" for ch in target.lower())[:60]
                    result = automate_github_pull_request(
                        suggestion_type="Metadata",
                        file_name=f"humeta_profile_proposal_{safe_name}.txt",
                        file_content=payload,
                        title_summary=f"HuMeta profile proposal: {target}",
                    )
                (st.error if "❌" in result else st.success)(result)
