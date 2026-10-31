# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 3: Community Data Repository Sync."""

from __future__ import annotations
import streamlit as st
import pandas as pd
import io
import json
import os
import time
import uuid
from pathlib import Path
from oem.vocab import (PUBLIC_DATASET_MAX_MB)
from oem.app.common import (load_published_datasets, open_review_pull_request, safe_slug)


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    st.header("🌐 Public Dataset Library")
    st.caption(
        "Browse datasets researchers have published, or submit a de-identified dataset for "
        "public release. Submissions are reviewed by a maintainer before they are listed."
    )
    st.info(
        "🔒 **Private datasets are never stored.** To analyze data you can't make public, use "
        "Module 4 and upload the file there: it is held in memory for your session only and "
        "is discarded when you leave or reload the page."
    )
    st.markdown("---")

    st.subheader("Published datasets")
    published_datasets = load_published_datasets()
    if not published_datasets:
        st.info("No datasets have been published yet.")
    else:
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Title": item.get("dataset_title", ""),
                        "Description": item.get("description", ""),
                        "License": item.get("license", ""),
                        "Rows": item.get("row_count", ""),
                        "Columns": item.get("column_count", ""),
                        "Published": item.get("submitted_at_utc", ""),
                    }
                    for item in published_datasets
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
        download_choice = st.selectbox(
            "Download a published dataset",
            published_datasets,
            format_func=lambda item: item.get("dataset_title") or item.get("csv_file"),
            key="module3_download_choice",
        )
        st.download_button(
            "Download CSV",
            data=Path(download_choice["_csv_path"]).read_bytes(),
            file_name=os.path.basename(download_choice["_csv_path"]),
            mime="text/csv",
        )

    st.markdown("---")
    st.subheader("Submit a dataset for public release")
    st.warning(
        "Public release is permanent in practice: once merged, the file is downloadable by anyone "
        "and remains in the repository's history even if later removed. Review consent, IRB "
        "requirements, data-use agreements, ownership, and disclosure risk with the appropriate "
        "people first. These confirmations are not approval or a guarantee that data are safe to share."
    )
    check_authority = st.checkbox(
        "I have permission from the data owner and applicable consent/approvals for public release."
    )
    check_identifiers = st.checkbox(
        "I removed direct and indirect identifiers and reviewed sensitive fields and small groups."
    )
    public_release_confirmed = st.checkbox(
        "I understand the dataset will be public and cannot be fully retracted."
    )
    dataset_title = st.text_input("Dataset title", placeholder="e.g., First-year student engagement survey (de-identified)")
    dataset_description = st.text_area(
        "Short description",
        placeholder="What was collected, from whom (in general terms), when, and how variables are coded.",
    )
    dataset_license = st.selectbox(
        "License",
        ["CC BY 4.0", "CC0 1.0 (public domain)", "CC BY-NC 4.0", "Other (describe in description)"],
    )
    uploaded_data_file = st.file_uploader(
        "Choose a de-identified dataset (.csv)",
        type=["csv"],
        max_upload_size=PUBLIC_DATASET_MAX_MB,
        help=f"CSV files up to {PUBLIC_DATASET_MAX_MB} MB.",
    )

    if uploaded_data_file is not None:
        try:
            uploaded_bytes = uploaded_data_file.getvalue()
            df_user_raw = pd.read_csv(io.BytesIO(uploaded_bytes))
            if df_user_raw.empty:
                raise ValueError("The uploaded CSV has no data rows.")
            st.success("CSV parsed successfully. Review the preview before submitting.")
            st.dataframe(df_user_raw.head(10), use_container_width=True)
            st.caption(
                f"{len(df_user_raw):,} rows · {len(df_user_raw.columns):,} columns · "
                f"{len(uploaded_bytes) / (1024 * 1024):.2f} MB"
            )

            ready_to_submit = (
                bool(dataset_title.strip())
                and check_authority
                and check_identifiers
                and public_release_confirmed
            )
            if not ready_to_submit:
                st.warning("Enter a title and complete all confirmations before submitting.")
            if st.button(
                "Submit dataset for public release",
                type="primary",
                disabled=publish_disabled or not ready_to_submit,
                help=publish_hint,
            ):
                dataset_id = uuid.uuid4().hex[:10]
                base_name = f"{safe_slug(dataset_title, 'dataset', 50)}-{dataset_id}"
                metadata_record = {
                    "schema_version": 1,
                    "dataset_id": dataset_id,
                    "dataset_title": dataset_title.strip(),
                    "description": dataset_description.strip(),
                    "license": dataset_license,
                    "csv_file": f"{base_name}.csv",
                    "original_file_name": os.path.basename(uploaded_data_file.name),
                    "row_count": len(df_user_raw),
                    "column_count": len(df_user_raw.columns),
                    "columns": [str(column) for column in df_user_raw.columns],
                    "byte_size": len(uploaded_bytes),
                    "submitted_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                with st.spinner("Opening a pull request for maintainer review..."):
                    result_message = open_review_pull_request(
                        suggestion_type="Public Dataset",
                        title_summary=dataset_title.strip()[:120],
                        files={
                            f"published/datasets/{base_name}.csv": uploaded_bytes,
                            f"published/datasets/{base_name}.json": json.dumps(
                                metadata_record, ensure_ascii=False, indent=2
                            ),
                        },
                        description=(
                            "Public dataset submission. The submitter confirmed permission, "
                            "de-identification, and understanding that release is public. "
                            "**Inspect the CSV for identifiers before merging.**"
                        ),
                    )
                (st.error if "❌" in result_message else st.success)(result_message)
        except pd.errors.EmptyDataError:
            st.error("The uploaded CSV is empty or does not contain a readable header row.")
        except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as e:
            st.error(f"Could not parse the uploaded CSV: {e}")
        except Exception as e:
            st.error(f"Error reading uploaded dataset: {e}")
