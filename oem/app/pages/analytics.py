# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 5: Descriptive & Scale Analytics, organized by the constructs in the variable plan.

Columns are matched to the plan by their shared variable names; each construct's
measure becomes a scale with descriptives, a score, and reliability; scale
scores are correlated. Statistics come from pingouin (see ``oem/analysis.py``),
and an R script reproduces everything with the psych package. Private data stay
in memory for this session only.
"""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from oem import analysis as A
from oem import plan as P
from oem import recommend as R
from oem.app.common import current_project, load_published_datasets, open_review_pull_request, public_submission_warning
from oem.app.profile_form import library

PRIVATE = "Upload my dataset (.csv): analyzed in this session only, never stored"
PUBLISHED = "Use a published public dataset"
EXAMPLE = "Use example data shaped like my variable plan (synthetic, not research data)"
TOOLS = [
    ("R", "https://www.r-project.org/", "free statistics software; the downloadable script uses it"),
    ("psych (R package)", "https://CRAN.R-project.org/package=psych", "reliability (alpha, omega), scale scoring, factor analysis"),
    ("lavaan (R package)", "https://lavaan.ugent.be/", "confirmatory factor analysis and structural equation models"),
    ("JASP", "https://jasp-stats.org/", "free point-and-click statistics built on R, including reliability and factor analysis"),
    ("jamovi", "https://www.jamovi.org/", "free point-and-click statistics built on R"),
    ("pingouin (Python)", "https://pingouin-stats.org/", "the package this module uses"),
]


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    lib = library()
    st.header("5. Descriptive & Scale Analytics")
    st.caption(
        "Analyze your data by construct, using the variable plan from Module 2. Columns are matched to your plan by "
        "their shared variable names. Each construct gets descriptives, a scale score, and reliability, and scale "
        "scores are correlated. Statistics are computed with pingouin, a peer-reviewed open-source package, and you "
        "can download an R script that reproduces them."
    )
    plan = P.normalize(current_project().get("module2_plan"), lib)
    has_plan = bool(plan["measures"])

    # ------------------------------------------------------------ Step 1
    st.subheader("Step 1 · Data")
    options = [PRIVATE] + ([PUBLISHED] if load_published_datasets() else []) + ([EXAMPLE] if has_plan else [])
    source = st.radio("Data to analyze", options, key="m5_source")
    df = None
    if source == PRIVATE:
        st.caption("🔒 Your file is read into memory for this browser session only. It is not saved, uploaded to "
                   "GitHub, or shared, and it is discarded when you reload or leave the page.")
        upload = st.file_uploader("Your dataset (.csv)", type=["csv"], key="m5_upload")
        if upload is not None:
            try:
                df = pd.read_csv(upload)
            except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as error:
                st.error(f"Could not read the CSV: {error}")
    elif source == PUBLISHED:
        datasets = load_published_datasets()
        chosen = st.selectbox("Published dataset", datasets, key="m5_published",
                              format_func=lambda d: f"{d.get('dataset_title') or d.get('csv_file')} ({d.get('row_count', '?')} rows)")
        try:
            df = pd.read_csv(chosen["_csv_path"])
        except (KeyError, TypeError, OSError, pd.errors.EmptyDataError, pd.errors.ParserError) as error:
            st.error(f"Could not load the dataset: {error}")
    else:
        st.info("Example data are synthetic, generated to look like your plan's codebook. Use them to try the module, "
                "not for research.")
        df = A.example_data(lib, plan)
    if df is None or df.empty:
        if not has_plan:
            st.caption("Tip: save a variable plan in Module 2 so columns are matched to your constructs automatically.")
        _other_tools()
        _recommend_analysis(publish_disabled, publish_hint)
        return
    st.caption(f"{len(df):,} rows · {len(df.columns):,} columns")
    with st.expander("Preview the first rows"):
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    # ------------------------------------------------------------ Step 2
    st.subheader("Step 2 · Match columns to your variable plan")
    columns = list(df.columns)
    if has_plan:
        scales, standard, unmatched = A.match_columns(lib, plan, columns)
        st.dataframe(pd.DataFrame([{"Scale (construct: measure)": s.label, "Matched columns": len(s.columns),
                                    "Expected": len(s.expected), "Not found": ", ".join(s.missing[:6]) + (" …" if len(s.missing) > 6 else "")}
                                   for s in scales]), use_container_width=True, hide_index=True)
        if standard:
            st.caption("Standard variables found: " + ", ".join(standard))
        st.caption("Columns are matched by the variable names in your codebook. Adjust any scale below if your file uses "
                   "different names." + (f" Columns not in the plan: {', '.join(unmatched[:12])}" + (" …" if len(unmatched) > 12 else "")
                                         if unmatched else ""))
        with st.expander("Adjust which columns belong to each scale"):
            for s in scales:
                s.columns = st.multiselect(s.label, columns, default=s.columns, key=f"m5_cols_{s.key}")
    else:
        st.info("No variable plan in your project. Build one in Module 2 so columns are matched to your constructs "
                "automatically, or define scales here.")
        count = st.number_input("How many scales?", min_value=1, max_value=20, value=1, step=1, key="m5_nscales")
        scales = []
        for i in range(int(count)):
            c1, c2 = st.columns([1, 3])
            name = c1.text_input(f"Scale {i + 1} name", value=f"Scale {i + 1}", key=f"m5_name_{i}")
            chosen = c2.multiselect(f"Columns in scale {i + 1}", columns, key=f"m5_manual_{i}")
            if chosen:
                scales.append(A.manual_scale(name, chosen))
    scales = [s for s in scales if s.columns]
    if not scales:
        st.warning("No columns are matched to a scale yet.")
        _other_tools()
        _recommend_analysis(publish_disabled, publish_hint)
        return

    # ------------------------------------------------------------ Step 3
    st.subheader("Step 3 · Results by construct")
    method = st.radio("Scale score", list(A.SCORE_METHODS), format_func=A.SCORE_METHODS.get, horizontal=True, key="m5_method")
    scores = pd.DataFrame(index=df.index)
    reliabilities: dict[str, dict] = {}
    try:
        for s in scales:
            st.markdown(f"#### {s.label}")
            data = A.items(df, s)
            if s.data_type == "binary":
                st.caption("Codes in a coding scheme: how often each code is present.")
                st.dataframe(A.prevalence(df, s).round(1), use_container_width=True, hide_index=True)
                continue
            scores[s.label] = A.score(df, s, method)
            rel = A.reliability(data)
            reliabilities[s.key] = rel
            c1, c2, c3 = st.columns(3)
            c1.metric("Average scale score", f"{scores[s.label].mean():.2f}", help=f"SD {scores[s.label].std():.2f}; "
                      f"{int(scores[s.label].notna().sum())} rows with a score")
            c2.metric("Items", rel["items"])
            if rel["alpha"] is not None:
                c3.metric("Cronbach's alpha", f"{rel['alpha']:.2f}", help=f"95% CI {rel['ci_low']:.2f} to {rel['ci_high']:.2f}; "
                          f"{rel['n']} complete cases. Interpret in light of the instrument, sample, and context.")
            else:
                c3.metric("Cronbach's alpha", "—", help="Needs at least two items and three complete cases.")
            with st.expander("Item statistics"):
                st.dataframe((rel["item_stats"] if not rel["item_stats"].empty else A.descriptives(data)).round(3),
                             use_container_width=True, hide_index=True)
    except RuntimeError as error:
        st.error(str(error))
        return

    # ------------------------------------------------------------ Step 4
    st.subheader("Step 4 · Relationships between scale scores")
    corr_method = st.radio("Correlation", ["pearson", "spearman"], format_func=str.capitalize, horizontal=True, key="m5_corr",
                           help="Spearman suits ordinal or skewed scores; Pearson suits roughly continuous, linear relationships.")
    corr_table = pd.DataFrame()
    if scores.shape[1] >= 2:
        corr_table = A.correlations(scores, corr_method)
        matrix = A.correlation_matrix(scores, corr_method)
        st.dataframe(matrix.style.background_gradient(cmap="coolwarm", vmin=-1, vmax=1).format("{:.2f}"),
                     use_container_width=True)
        st.dataframe(corr_table.round(3), use_container_width=True, hide_index=True)
    else:
        st.caption("Correlations need at least two scale scores.")
    score_desc = A.descriptives(scores)

    # ------------------------------------------------------------ Step 5
    st.subheader("Step 5 · Download and reproduce")
    st.caption(f"Statistics: {A.PINGOUIN_CITATION}")
    tables = A.results_tables(scales, reliabilities, corr_table)
    d1, d2, d3, d4 = st.columns(4)
    d1.download_button("Scale scores (CSV)", scores.to_csv(index=False).encode("utf-8"), file_name="scale_scores.csv",
                       mime="text/csv", key="m5_dl_scores",
                       help="Scores for each row of your data. Keep this file as private as the data.")
    results = io.StringIO()
    for name, frame in tables.items():
        results.write(f"# {name}\n")
        frame.to_csv(results, index=False)
        results.write("\n")
    d2.download_button("Results tables (CSV)", results.getvalue().encode("utf-8"), file_name="module5_results.csv",
                       mime="text/csv", key="m5_dl_results")
    try:
        pdf = A.pdf_report("HuMeta Portal: Module 5 results", len(df), scales, score_desc, reliabilities, corr_table, method)
        d3.download_button("Report (PDF)", pdf, file_name="module5_report.pdf", mime="application/pdf", key="m5_dl_pdf")
    except Exception as error:  # reportlab problems should not hide the results
        d3.caption(f"PDF unavailable: {error}")
    d4.download_button("R script (psych)", A.r_script(scales, method, corr_method).encode("utf-8"),
                       file_name="module5_analysis.R", mime="text/plain", key="m5_dl_r",
                       help="Reproduces these analyses in R on your own computer, including McDonald's omega.")
    _other_tools()
    _recommend_analysis(publish_disabled, publish_hint)


def _other_tools() -> None:
    with st.expander("Other free tools for these analyses"):
        for name, url, what in TOOLS:
            st.markdown(f"- [{name}]({url}): {what}")


def _recommend_analysis(publish_disabled: bool, publish_hint: str | None) -> None:
    with st.expander("💡 Recommend an analysis for this module"):
        st.caption("Suggest an analysis researchers need here (for example McDonald's omega, confirmatory factor "
                   "analysis, or measurement invariance). Recommendations are reviewed, and accepted analyses are "
                   "implemented with an established open-source package.")
        public_submission_warning()
        with st.form("m5_recommend_analysis"):
            name = st.text_input("Analysis *")
            purpose = st.text_area("What does it tell researchers? *")
            when = st.text_area("When should it be used? (optional)")
            software = st.text_input("R or Python package and function, if you know one (optional)",
                                     placeholder="e.g., psych::omega, lavaan::cfa")
            c1, c2 = st.columns(2)
            citation = c1.text_input("Methods citation (optional)")
            doi = c2.text_input("DOI (optional)")
            consent = st.checkbox("I confirm this recommendation contains no confidential information and may be published.")
            submitted = st.form_submit_button("Submit recommendation", disabled=publish_disabled, help=publish_hint)
        if submitted:
            rec = R.analysis_recommendation(name=name, purpose=purpose, when_to_use=when, software=software,
                                            citation=citation, doi=doi)
            issues = R.analysis_problems(rec) + ([] if consent else ["Tick the confirmation box."])
            for issue in issues:
                st.error(issue)
            if not issues:
                path, content = R.file_for(rec)
                with st.spinner("Opening a pull request for review..."):
                    message = open_review_pull_request(suggestion_type="Analysis recommendation", title_summary=R.title_for(rec),
                                                       files={path: content}, description=R.pr_description(rec))
                (st.error if "❌" in message else st.success)(message)
