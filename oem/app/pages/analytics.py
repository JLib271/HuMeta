# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 5: Descriptive & Scale Analytics."""

from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
import io
import uuid
from oem import plan as plan_model
from oem.app.common import (automate_github_pull_request, current_project, load_published_datasets, public_submission_warning)
from oem.library import Library


def render(*, signed_in: bool, publish_disabled: bool, publish_hint: str | None) -> None:
    st.header("📊 Descriptive & Scale Analytics")
    st.caption(
        "Analyze dataset columns in the context of your Module 2 framework-derived, "
        "demographic/contextual, and custom variable matrix."
    )
    st.markdown("---")
    
    # Ingest Data Sheet Mapping Workspace
    st.subheader("📂 1. Ingest Data Sheet Mapping Workspace")
    private_source = "Upload a private dataset (.csv) — analyzed in this session only, never stored"
    published_source = "Use a published public dataset"
    synthetic_source = "Use Standard Synthetic Sample Dataset"
    available_datasets = load_published_datasets()
    data_source_options = [private_source]
    if available_datasets:
        data_source_options.append(published_source)
    data_source_options.append(synthetic_source)
    data_source = st.radio("Analytics Dataset Source Selection:", data_source_options)

    st.info(
        "There are no required column names. Use the variable matrix from Module 2 to map "
        "numeric columns for scores and categorical columns for response distributions. "
        "The dataset needs at least one numeric analysis variable."
    )
    manifest_upload = st.file_uploader(
        "Optional: upload the variable matrix from Module 2 (CSV)",
        type=["csv"],
        key="analytics_module2_manifest_upload",
        help="Use the variable matrix downloaded in Module 2. The variable plan in your project is loaded automatically.",
    )
    module2_manifest = st.session_state.get("module2_variable_manifest", [])
    saved_plan = current_project().get("module2_plan") or {}
    if not module2_manifest and saved_plan.get("schema_version", 1) >= 2:
        module2_manifest = plan_model.manifest(Library.load(), plan_model.normalize(saved_plan))
    if manifest_upload is not None:
        try:
            imported_manifest = pd.read_csv(manifest_upload)
            required_manifest_fields = {"Variable_ID", "Variable_Label", "Framework_Source"}
            if required_manifest_fields.issubset(imported_manifest.columns) and (
                {"Construct", "Concept_Construct"} & set(imported_manifest.columns)
            ):
                module2_manifest = imported_manifest.fillna("").to_dict(orient="records")
                st.success(f"Loaded {len(module2_manifest)} variables from the Module 2 matrix.")
            else:
                st.error(
                    "The uploaded file is not a variable matrix from Module 2. It must include "
                    "Variable_ID, Variable_Label, Framework_Source, and Construct."
                )
        except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as matrix_error:
            st.error(f"Could not read the variable matrix: {matrix_error}")
    
    st.markdown("---")
    df_analytics = None
    
    if data_source == published_source and available_datasets:
        try:
            selected_dataset = st.selectbox(
                "Select a dataset",
                available_datasets,
                format_func=lambda item: (
                    f"{item.get('dataset_title') or item.get('csv_file')} "
                    f"({item.get('row_count', '?')} rows)"
                ),
                key="analytics_dataset_id"
            )
            df_analytics = pd.read_csv(selected_dataset["_csv_path"])
            st.info(f"Analyzing the published dataset `{selected_dataset.get('csv_file')}`.")
        except (KeyError, TypeError, OSError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
            st.error(f"Could not load the selected published dataset: {e}")
    elif data_source == synthetic_source:
        st.info("This is synthetic demonstration data, not observed research data.")
        np.random.seed(42)
        n_samples = 100
        synthetic_data = {
            "Participant_ID": range(1, n_samples + 1),
            "Example_Context_Group": np.random.choice(
                ["Group A", "Group B"], size=n_samples
            ),
            "Example_Input_Item_1": np.random.choice([1, 2, 3, 4, 5], size=n_samples),
            "Example_Input_Item_2": np.random.choice([1, 2, 3, 4, 5], size=n_samples),
            "Example_Experience_Item_1": np.random.choice([1, 2, 3, 4, 5], size=n_samples),
            "Example_Outcome_Item_1": np.random.choice([1, 2, 3, 4, 5], size=n_samples),
            "Example_Outcome_Item_2": np.random.choice([1, 2, 3, 4, 5], size=n_samples),
            "Example_Context_Score": np.random.randint(0, 10, size=n_samples),
        }
        df_analytics = pd.DataFrame(synthetic_data)
    else:
        st.caption(
            "🔒 Your file is read into memory for this browser session only. It is not saved, "
            "uploaded to GitHub, or shared, and it is discarded when you reload or leave the page."
        )
        uploaded_analytics_file = st.file_uploader(
            "Upload your dataset (.csv)", type=["csv"], key="analytics_private_upload"
        )
        if uploaded_analytics_file is not None:
            try:
                df_analytics = pd.read_csv(uploaded_analytics_file)
            except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError) as e:
                st.error(f"Could not read the uploaded CSV: {e}")

    if df_analytics is not None:
        numeric_columns = df_analytics.select_dtypes(include=[np.number]).columns
        if not any("ID" not in column for column in numeric_columns):
            st.warning("This dataset has no numeric analysis variables (excluding ID fields).")
            df_analytics = None
            
    if df_analytics is not None:
        st.subheader("📋 Dataset Workspace Snapshot")
        st.dataframe(df_analytics.head(10), use_container_width=True, hide_index=True)
        
        all_numeric_cols = df_analytics.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in all_numeric_cols if "ID" not in c.upper()]
        analysis_columns = [
            column for column in df_analytics.columns
            if "ID" not in column.upper()
        ]

        st.divider()
        st.subheader("📐 2. Map dataset columns to Module 2 variables")
        computed_scales_manifest = {}
        mapped_categorical_variables = {}
        if module2_manifest:
            module2_variables = [
                row for row in module2_manifest
                if str(row.get("Variable_ID", "")).strip()
                and (
                    str(row.get("Variable_Label", "")).strip()
                    or str(row.get("Construct") or row.get("Concept_Construct") or "").strip()
                )
            ]
            if module2_variables and analysis_columns:
                mapping_df = pd.DataFrame([
                    {
                        "Variable_ID": str(row.get("Variable_ID", "")),
                        "Variable": str(row.get("Variable_Label") or row.get("Construct") or row.get("Concept_Construct") or ""),
                        "Framework / source": str(row.get("Framework_Source", "")),
                        "Dataset columns": [],
                    }
                    for row in module2_variables
                ])
                st.caption(
                    "Choose dataset column(s) that represent each Module 2 variable. Numeric columns "
                    "can be combined into scores; categorical columns are summarized as response counts. "
                    "Mappings are researcher-defined, not inferred from column names."
                )
                mapping_source = (
                    str(selected_dataset.get("dataset_id", ""))
                    if data_source == published_source
                    else data_source
                )
                mapping_identity = uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{mapping_source}|{','.join(analysis_columns)}",
                ).hex[:12]
                mapping_df = st.data_editor(
                    mapping_df,
                    key=f"module4_variable_mapping_{mapping_identity}",
                    hide_index=True,
                    use_container_width=True,
                    disabled=["Variable_ID", "Variable", "Framework / source"],
                    column_config={
                        "Dataset columns": st.column_config.MultiselectColumn(
                            "Dataset columns",
                            options=analysis_columns,
                            help="Select numeric item columns for a composite, or a categorical column for response counts.",
                        ),
                    },
                )
                for _, mapping in mapping_df.iterrows():
                    mapping_columns = mapping["Dataset columns"]
                    if not isinstance(mapping_columns, list):
                        mapping_columns = []
                    selected_items = [
                        column for column in mapping_columns
                        if column in analysis_columns
                    ]
                    if not selected_items:
                        continue
                    numeric_items = [
                        column for column in selected_items if column in numeric_cols
                    ]
                    categorical_items = [
                        column for column in selected_items if column not in numeric_cols
                    ]
                    variable_id = str(mapping["Variable_ID"])
                    score_column = (
                        "Module2_" + "".join(
                            char if char.isalnum() else "_" for char in variable_id
                        ).strip("_")
                    )
                    variable_label = str(mapping["Variable"])
                    variable_manifest_row = next(
                        (row for row in module2_variables if str(row["Variable_ID"]) == variable_id),
                        {},
                    )
                    if numeric_items:
                        df_analytics[score_column] = df_analytics[numeric_items].mean(axis=1)
                        scale_properties = {
                            "column": score_column,
                            "items": numeric_items,
                            "label": variable_label,
                            "framework": str(variable_manifest_row.get("Framework_Source", "")),
                        }
                    else:
                        scale_properties = None
                    if len(numeric_items) >= 2:
                        clean_items = df_analytics[numeric_items].dropna()
                        if len(clean_items) > 1:
                            item_variances = clean_items.var(ddof=1, axis=0).sum()
                            total_variance = clean_items.sum(axis=1).var(ddof=1)
                            if total_variance > 0:
                                alpha_val = (
                                    len(numeric_items) / (len(numeric_items) - 1)
                                ) * (1 - item_variances / total_variance)
                                scale_properties["alpha"] = alpha_val
                    if scale_properties:
                        computed_scales_manifest[variable_id] = scale_properties
                    if categorical_items:
                        mapped_categorical_variables[variable_id] = {
                            "label": variable_label,
                            "columns": categorical_items,
                            "framework": str(variable_manifest_row.get("Framework_Source", "")),
                        }
                mapped_variable_count = (
                    len(computed_scales_manifest) + len(mapped_categorical_variables)
                )
                if mapped_variable_count:
                    st.success(
                        f"Mapped {mapped_variable_count} Module 2 variable(s) to observed dataset columns."
                    )
            else:
                st.info("The Module 2 matrix has no variables to map, or this dataset has no usable columns.")
        else:
            st.info(
                "To map analytics to your study framework, save a variable plan in Module 2 or "
                "upload its variable matrix (CSV) above."
            )
        if mapped_categorical_variables:
            st.markdown("**Categorical Module 2 variable response counts**")
            for variable in mapped_categorical_variables.values():
                for column in variable["columns"]:
                    st.caption(f"{variable['label']} — `{column}`")
                    counts = (
                        df_analytics[column]
                        .fillna("Missing")
                        .value_counts()
                        .rename_axis("Response")
                        .reset_index(name="Count")
                    )
                    st.dataframe(counts, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("📊 3. Variable Distribution Explorer")
        if numeric_cols:
            selected_col = st.selectbox("Select Target Variable for Distribution Evaluation:", numeric_cols)
            
            col_chart1, col_chart2 = st.columns([1, 2])
            with col_chart1:
                desc_stats = df_analytics[selected_col].describe()
                st.markdown(f"**Descriptive Vectors for `{selected_col}`:**")
                st.dataframe(pd.DataFrame(desc_stats), use_container_width=True)
            with col_chart2:
                counts_df = df_analytics[selected_col].value_counts().sort_index().reset_index()
                counts_df.columns = ["Response Categories", "Frequency (Participant Count)"]
                
                st.markdown(f"**Response Value Counts for `{selected_col}`**")
                st.bar_chart(counts_df.set_index("Response Categories"), y="Frequency (Participant Count)", use_container_width=True)
        
        st.divider()
        st.subheader("🧮 4. Module 2 Variable Scores and Reliability")
        st.caption(
            "Composite scores use the selected numeric columns. Internal consistency is calculated "
            "only for variables mapped to two or more items; it is not inferred from framework names."
        )
        scale_summary_text = "=== CRONBACH'S ALPHA INTERNAL CONSISTENCY PROFILE ===\n"
        variables_with_alpha = [
            (variable_id, properties)
            for variable_id, properties in computed_scales_manifest.items()
            if "alpha" in properties
        ]
        if variables_with_alpha:
            for variable_id, properties in variables_with_alpha:
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric(
                        label=f"{properties['label']} Mean Score",
                        value=f"{df_analytics[properties['column']].mean():.2f}",
                    )
                with col_m2:
                    st.metric(
                        label=f"{properties['label']} Cronbach's Alpha (α)",
                        value=f"{properties['alpha']:.3f}",
                        help="Interpret reliability in light of the instrument, sample, and study context.",
                    )
                scale_summary_text += (
                    f"Variable: {properties['label']} ({variable_id})\n"
                    f"Framework: {properties['framework']}\n"
                    f"Mapped items: {', '.join(properties['items'])}\n"
                    f"Cronbach's alpha: {properties['alpha']:.4f}\n\n"
                )
        elif computed_scales_manifest:
            st.info(
                "Mapped variables have single items only. Cronbach's alpha requires at least "
                "two items for a variable."
            )
        else:
            st.info(
                "Map Module 2 variables to dataset columns above to calculate theory-aligned "
                "composite scores and reliability."
            )

        st.divider()
        st.subheader("🔗 5. Variable Relationship Matrix")
        correlation_method = st.selectbox(
            "Correlation method",
            options=["Spearman", "Pearson"],
            help="Spearman is appropriate for ordinal/ranked data; Pearson is for suitable continuous measures.",
            key="analytics_correlation_method",
        )
        correlation_targets = [
            properties["column"] for properties in computed_scales_manifest.values()
        ]
        correlation_targets.extend(
            column for column in numeric_cols if column not in correlation_targets
        )
        
        if len(correlation_targets) >= 2:
            correlation_matrix = df_analytics[correlation_targets].corr(
                method=correlation_method.lower()
            )
            friendly_labels = {
                column: properties["label"]
                for properties in computed_scales_manifest.values()
                for column in [properties["column"]]
            }
            clean_corr_matrix = correlation_matrix.rename(index=friendly_labels, columns=friendly_labels)
            
            st.markdown(f"**{correlation_method} Correlation Matrix:**")
            st.dataframe(clean_corr_matrix.style.background_gradient(cmap="coolwarm", axis=None).format("{:.3f}"), use_container_width=True)
        else:
            st.warning("Select or map at least two numeric variables to build a correlation matrix.")
            clean_corr_matrix = pd.DataFrame()

        st.divider()
        st.subheader("📥 6. Download Evaluation Compendium")
        st.caption("Generate a compiled analytical summary PDF handbook detailing item statistics, alpha metrics, and active distribution data charts.")

        pdf_buffer = io.BytesIO()
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            import matplotlib.pyplot as plt
            
            fig_dist, ax_dist = plt.subplots(figsize=(6, 3))
            counts_df.plot(kind="bar", x="Response Categories", y="Frequency (Participant Count)", ax=ax_dist, color="#1f77b4", legend=False)
            ax_dist.set_title(f"Distribution: {selected_col}")
            ax_dist.set_xlabel("Response Categories")
            ax_dist.set_ylabel("Frequency")
            plt.tight_layout()
            
            # Charts stay in memory: they are derived from possibly private data
            # and a shared temp path would mix up concurrent users' reports.
            dist_img_path = io.BytesIO()
            fig_dist.savefig(dist_img_path, format="png", dpi=200)
            dist_img_path.seek(0)
            plt.close(fig_dist)
            
            corr_img_path = None
            if not clean_corr_matrix.empty:
                fig_corr, ax_corr = plt.subplots(figsize=(5, 4))
                cax = ax_corr.matshow(clean_corr_matrix, cmap="coolwarm", vmin=-1, vmax=1)
                fig_corr.colorbar(cax)
                
                ticks = np.arange(len(clean_corr_matrix.columns))
                ax_corr.set_xticks(ticks)
                ax_corr.set_yticks(ticks)
                ax_corr.set_xticklabels(clean_corr_matrix.columns, rotation=45, ha="left", fontsize=8)
                ax_corr.set_yticklabels(clean_corr_matrix.index, fontsize=8)
                ax_corr.set_title(f"{correlation_method} Correlation Matrix", pad=20)
                plt.tight_layout()
                
                corr_img_path = io.BytesIO()
                fig_corr.savefig(corr_img_path, format="png", dpi=200)
                corr_img_path.seek(0)
                plt.close(fig_corr)

            doc = SimpleDocTemplate(
                pdf_buffer, 
                pagesize=letter,
                rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
                title="Open Educational Metadata Analysis Report"
            )
            
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'ReportTitle', parent=styles['Heading1'],
                fontSize=22, textColor=colors.HexColor("#1A365D"), spaceAfter=12
            )
            h2_style = ParagraphStyle(
                'SectionHeader', parent=styles['Heading2'],
                fontSize=14, textColor=colors.HexColor("#2B6CB0"), spaceBefore=14, spaceAfter=8
            )
            body_style = ParagraphStyle(
                'ReportBody', parent=styles['BodyText'],
                fontSize=10, leading=14, textColor=colors.HexColor("#2D3748")
            )

            story = []
            story.append(Paragraph("<b>Open Educational Metadata Report Compendium</b>", title_style))
            story.append(Paragraph(f"<b>Dataset Sample Metric Matrix Size:</b> {df_analytics.shape[0]} Rows | {df_analytics.shape[1]} Columns", body_style))
            story.append(Spacer(1, 15))
            
            story.append(Paragraph("<b>1. Cronbach's Alpha Scale Reliability Internal Consistency</b>", h2_style))
            for line in scale_summary_text.split("\n"):
                if line.strip() and "CRONBACH" not in line:
                    story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 10))
            
            story.append(Paragraph(f"<b>2. Distribution Visualization Graph: {selected_col}</b>", h2_style))
            if dist_img_path is not None:
                story.append(Image(dist_img_path, width=320, height=160))
            story.append(Spacer(1, 15))
            
            if not clean_corr_matrix.empty and corr_img_path is not None:
                story.append(Paragraph("<b>3. Mixed Multi-Variable Inter-Correlation Matrix</b>", h2_style))
                corr_data = [["Variable"] + list(clean_corr_matrix.columns)]
                for idx, row in clean_corr_matrix.iterrows():
                    corr_data.append([str(idx)] + [f"{val:.3f}" for val in row])
                
                corr_table = Table(corr_data, hAlign='LEFT')
                corr_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#1A202C")),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 8),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
                ]))
                story.append(corr_table)
                story.append(Spacer(1, 15))
                story.append(Paragraph("<b>Correlation Map Matrix Diagram:</b>", body_style))
                story.append(Image(corr_img_path, width=240, height=192))
                story.append(Spacer(1, 15))
                
            story.append(Paragraph("<b>4. Global Item Descriptive Metric Summaries Annex</b>", h2_style))
            desc_df = df_analytics[numeric_cols].describe().round(3).reset_index()
            desc_data = [list(desc_df.columns)] + desc_df.values.tolist()
            
            string_desc_data = []
            for row in desc_data:
                string_desc_data.append([f"{item:.3f}" if isinstance(item, (int, float)) else str(item) for item in row])
                
            desc_table = Table(string_desc_data, hAlign='LEFT')
            desc_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 7),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ]))
            story.append(desc_table)

            doc.build(story)
            
                
            st.download_button(
                label="📥 Download Complete Analytical Summary Report (.pdf)",
                data=pdf_buffer.getvalue(),
                file_name="educational_analytics_summary_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        except Exception as pdf_error:
            st.error(f"Failed to assemble PDF Report Compendium structure: {pdf_error}. Ensure reportlab and matplotlib packages exist.")
    else:
        st.warning("No continuous numeric variable items identified in the targeted workspace tracking file sheet.")

# --- MODULE 4 ANALYTICS SUGGESTION PIPELINE BUTTON ---
    st.markdown("---")
    st.markdown("### 🚀 Propose Alternative Statistical & Analytical Functions")
    st.caption("Seeking custom calculations? Enter a metric or statistical test title below. If you don't know the code, our system will auto-generate a Python template for you!")
    
    public_submission_warning()
    suggested_stat_metric = st.text_input("Proposed Statistical Function Title", placeholder="e.g., Two-Way ANOVA, Chi-Square Test", key="mod4_metric")
    suggested_stat_code = st.text_area("Proposed Python Code block (Optional)", placeholder="Leave blank to let the system auto-create the statistical calculation template...", height=100, key="mod4_code")
    
    if suggested_stat_metric:
        if st.button(
            "🚀 Push Function to GitHub as Pull Request",
            key="submit_mod4_pr_btn",
            disabled=publish_disabled,
            help=publish_hint,
        ):
            with st.spinner("Analyzing request and auto-generating statistical code block..."):
                
                # 1. AUTO-GENERATION ENGINE: Check if the user left the code block blank
                final_code_block = suggested_stat_code.strip()
                if not final_code_block:
                    metric_lower = suggested_stat_metric.lower()
                    
                    # Programmatic boilerplate generation rules based on common research models
                    if "anova" in metric_lower:
                        final_code_block = (
                            "import statsmodels.api as sm\n"
                            "from statsmodels.formula.api import ols\n\n"
                            "def calculate_custom_anova(df, dependent_var, independent_vars):\n"
                            "    # Auto-generated ANOVA formula wrapper\n"
                            "    formula = f'{dependent_var} ~ C({independent_vars[0]}) * C({independent_vars[1]})'\n"
                            "    model = ols(formula, data=df).fit()\n"
                            "    anova_table = sm.stats.anova_lm(model, typ=2)\n"
                            "    return anova_table"
                        )
                    elif "chi" in metric_lower or "square" in metric_lower:
                        final_code_block = (
                            "from scipy.stats import chi2_contingency\n\n"
                            "def calculate_custom_chisquare(df, col1, col2):\n"
                            "    # Auto-generated Chi-Square contingency analyzer\n"
                            "    contingency_table = pd.crosstab(df[col1], df[col2])\n"
                            "    chi2, p, dof, expected = chi2_contingency(contingency_table)\n"
                            "    return {'chi2_stat': chi2, 'p_value': p, 'degrees_of_freedom': dof}"
                        )
                    elif "regression" in metric_lower:
                        final_code_block = (
                            "import statsmodels.api as sm\n\n"
                            "def calculate_custom_regression(df, y_col, x_cols):\n"
                            "    # Auto-generated Linear Regression (OLS) model\n"
                            "    X = sm.add_constant(df[x_cols])\n"
                            "    y = df[y_col]\n"
                            "    model = sm.OLS(y, X).fit()\n"
                            "    return model.summary()"
                        )
                    else:
                        # Standard fail-safe mathematical descriptive vector blueprint
                        final_code_block = (
                            "import numpy as np\n"
                            "import scipy.stats as stats\n\n"
                            f"def calculate_{suggested_stat_metric.lower().replace(' ', '_')}(data_vector):\n"
                            f"    # Standard evaluation model for {suggested_stat_metric}\n"
                            "    clean_data = data_vector[~np.isnan(data_vector)]\n"
                            "    metric_mean = np.mean(clean_data)\n"
                            "    metric_variance = np.var(clean_data)\n"
                            "    return {'mean': metric_mean, 'variance': metric_variance}"
                        )
                
                # 2. Package the payload safely into an isolated string block
                analytics_payload = (
                    f"**Analytics Engine Function Enhancement Proposal**\n\n"
                    f"**Target Statistical Metric:** {suggested_stat_metric}\n\n"
                    f"### PROPOSED PYTHON ALGORITHM CODE\n"
                    f"```text\n{final_code_block}\n```\n\n"
                    f"---\n*Submitted securely via the Descriptive & Scale Analytics Suggestion Pipeline Interface.*"
                )
                
                # 3. Fire your global PyGithub worker function
                safe_filename = f"analytics_proposal_{suggested_stat_metric.lower().replace(' ', '_')}.txt"
                summary_title = f"Add Analytics Metric: {suggested_stat_metric}"
                
                result_message = automate_github_pull_request(
                    suggestion_type="Analytics",
                    file_name=safe_filename,
                    file_content=analytics_payload,
                    title_summary=summary_title
                )
                
                if "❌" in result_message:
                    st.error(result_message)
                else:
                    st.success(result_message)
