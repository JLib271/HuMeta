import streamlit as st
import pandas as pd
import numpy as np
import json
import urllib.parse
import requests
import base64
import tempfile
import os
import sqlite3

# Mapping of theoretical frameworks to their standard psychometric constructs/variables
THEORY_MAP = {
    "Theory of Planned Behavior": [
        "Attitude Toward the Behavior | Construct | A person's favorable or unfavorable evaluation of the behavior",
        "Subjective Norms | Construct | Perceived social pressure to perform or not perform the behavior",
        "Perceived Behavioral Control | Construct | Perceived ease or difficulty of performing the behavior",
        "Behavioral Intention | Construct | Indication of an individual's readiness to perform a given behavior"
    ],
    "Self-Determination Theory": [
        "Autonomy | Construct | The need to feel in command of one's life and actions",
        "Competence | Construct | The need to feel effective in interacting with the environment",
        "Relatedness | Construct | The need to feel a sense of belonging and attachment to other people",
        "Intrinsic Motivation / Extrinsic Motivation | Construct | Internal drive versus external rewards/pressures"
    ],
    "Diffusion of Innovations Theory": [
        "Relative Advantage | Construct | The degree to which an innovation is perceived as better than the idea it supersedes",
        "Compatibility | Construct | How well the innovation aligns with the values, experiences, and needs of potential adopters",
        "Complexity | Construct | The degree to which an innovation is perceived as difficult to understand and use",
        "Trialability | Construct | The degree to which an innovation may be experimented with before a full commitment",
        "Observability | Construct | The distinct visibility of the results of an innovation to others"
    ],
    "Technology Acceptance Model": [
        "Perceived Usefulness (PU) | Construct | The degree to which a person believes a system enhances job performance",
        "Perceived Ease of Use (PEOU) | Construct | The degree to which a person believes a system is free of effort",
        "Attitude Toward Using | Construct | The user's evaluation of the desirability of employing the application",
        "Behavioral Intention to Use | Construct | The user's likelihood to adopt or continue using the technology"
    ],
    "Social Cognitive Theory": [
        "Self-Efficacy | Construct | One's belief in their capability to execute behaviors necessary to produce specific performance attainments",
        "Outcome Expectations | Construct | Beliefs about the consequences of specific actions",
        "Observational Learning (Modeling) | Construct | Acquiring information/behaviors by watching others",
        "Behavioral Capability | Construct | Knowledge and skill to perform a given behavior",
        "Reinforcement / Reciprocal Determinism | Construct | The dynamic interaction of person, environment, and behavior"
    ]
}

# --- UNIFIED DATABASE INITIALIZATION ---
# Fallback to local SQLite if a cloud database is not linked or fails in Streamlit Secrets
try:
    db_url = st.secrets["connections"]["sql"]["url"]
    shared_conn = st.connection("sql", type="sql", url=db_url)
except Exception as e:
    shared_conn = None

# Initialize default states so rendering handles don't crash
local_df = None
df_studies = pd.DataFrame()
df_vars = pd.DataFrame()

# Page Configuration Layout 
st.set_page_config(page_title="Open Educational Metadata Portal", layout="wide")
st.title("🔬 Open Educational Metadata Portal")
st.caption("An Open Source, Community-Driven Engine for Standardized Educational Research and Psychometrics.")

# Ensure local tables structure exists for offline mode sessions
def init_local_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS studies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            authors TEXT,
            abstract TEXT,
            keywords TEXT,
            theoretical_framework TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS variables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            study_id INTEGER,
            variable_name TEXT NOT NULL,
            variable_type TEXT,
            operational_definition TEXT,
            FOREIGN KEY(study_id) REFERENCES studies(id)
        );
    """)
    conn.commit()

# --- STEP 1: CHOOSE TARGET ENGINE WORKFLOW ---
st.sidebar.header("⚙️ Workspace Engine")
db_mode = st.sidebar.radio("Data Saving Destination:", ["Local Locked (SQLite File)", "Global Collaborative Hub"])

# Setup sandboxed local SQLite session tracking
if "local_db_path" not in st.session_state:
    temp_dir = tempfile.gettempdir()
    st.session_state.local_db_path = os.path.join(temp_dir, "opened_metadata_session.db")
    conn = sqlite3.connect(st.session_state.local_db_path)
    init_local_tables(conn)
    conn.close()

# --- STEP 2: USER METADATA SUBMISSION FORM ---
st.header("📝 Submit New Study Metadata")

with st.form("study_submission_form", clear_on_submit=True):
    st.subheader("Core Project Details")
    title = st.text_input("Study Title*", placeholder="e.g., Impact of Open Textbooks on Retention")
    authors = st.text_input("Author(s)", placeholder="e.g., Jane Doe, John Smith")
    abstract = st.text_area("Abstract", placeholder="Summary of the study's objective and design...")
    keywords = st.text_input("Keywords (comma separated)", placeholder="e.g., open education, OER, equity")
    
    st.divider()
    st.subheader("Theoretical & Conceptual Framework")
    
    # 1. Transform the input into a structured query with multi-selection capability
    selected_theories = st.multiselect(
        "Which theoretical framework(s) inform your study?",
        options=[
            "Theory of Planned Behavior", 
            "Self-Determination Theory", 
            "Diffusion of Innovations Theory",
            "Technology Acceptance Model", 
            "Social Cognitive Theory", 
            "Other"
        ]
    )
    
    # 2. Render an on-the-fly custom text window if 'Other' is picked by the user
    other_framework = ""
    if "Other" in selected_theories:
        other_framework = st.text_input("Please specify your alternative theoretical framework:")

    st.divider()
    st.subheader("Study Variables Layout")
    st.caption("Define the properties of what you are measuring. Checking frameworks above will automatically pre-populate known baseline constructs below.")

    # 3. Compute dynamic text string content matching selected models
    prepopulated_vars = []
    for theory in selected_theories:
        if theory in THEORY_MAP:
            prepopulated_vars.extend(THEORY_MAP[theory])
            
    # Fallback to defaults if no matching structural frames are selected
    if not prepopulated_vars:
        default_value = "Course Grade | Dependent Variable | Final numerical score percentage scaled 0-100\nTextbook Cost | Independent Variable | Total out of pocket dollar cost calculated at checkout"
    else:
        default_value = "\n".join(prepopulated_vars)

    # 4. Bind the generated variables directly as the default layout payload string
    variables_input = st.text_area(
        "List variables being collected (One per line format -> Name | Type | Operational Definition)",
        value=default_value,
        help="You can append, edit, or remove rows freely to customize your study's precise profile metrics.",
        height=250
    )
    
    submit_btn = st.form_submit_button("💾 Save Study Record")

    # Cleaned, unified, and perfectly indented submission logic block
    if submit_btn:
        if not title:
            st.error("Study Title is required.")
        else:
            # Gather checkbox values into a structured text string
            frameworks_to_save = [t for t in selected_theories if t != "Other"]
            if "Other" in selected_theories and other_framework.strip():
                frameworks_to_save.append(other_framework.strip())
                
            final_framework_string = ", ".join(frameworks_to_save) if frameworks_to_save else "None Specified"
                
            # Process variable strings into clean array matrix tuples
            parsed_variables = []
            for line in variables_input.strip().split("\n"):
                if "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    v_name = parts[0] if len(parts) > 0 else ""
                    v_type = parts[1] if len(parts) > 1 else "Not Specified"
                    v_def = parts[2] if len(parts) > 2 else "No definition provided"
                    if v_name:
                        parsed_variables.append((v_name, v_type, v_def))
                else:
                    if line.strip():
                        parsed_variables.append((line.strip(), "Not Specified", "No definition provided"))

            # --- ROUTING SAVE PATHWAYS ---
            if db_mode == "Local Locked (SQLite File)":
                conn = sqlite3.connect(st.session_state.local_db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO studies (title, authors, abstract, keywords, theoretical_framework) VALUES (?, ?, ?, ?, ?)",
                    (title, authors, abstract, keywords, final_framework_string)
                )
                study_id = cursor.lastrowid
                
                for var in parsed_variables:
                    cursor.execute(
                        "INSERT INTO variables (study_id, variable_name, variable_type, operational_definition) VALUES (?, ?, ?, ?)",
                        (study_id, var[0], var[1], var[2])
                    )
                conn.commit()
                conn.close()
                st.success("Successfully logged study to your temporary local instance!")
                st.rerun()
                
            elif db_mode == "Global Collaborative Hub":
                if shared_conn is not None:
                    from sqlalchemy import text
                    with shared_conn.session as session:
                        res = session.execute(
                            text("""INSERT INTO studies (title, authors, abstract, keywords, theoretical_framework) 
                                   VALUES (:title, :authors, :abstract, :keywords, :framework) RETURNING id;"""),
                            {"title": title, "authors": authors, "abstract": abstract, "keywords": keywords, "framework": final_framework_string}
                        )
                        try:
                            study_id = res.fetchone()[0]
                        except Exception:
                            study_id = session.execute(text("SELECT max(id) FROM studies;")).fetchone()[0]
                        
                        for var in parsed_variables:
                            session.execute(
                                text("""INSERT INTO variables (study_id, variable_name, variable_type, operational_definition) 
                                       VALUES (:study_id, :name, :type, :def);"""),
                                {"study_id": study_id, "name": var[0], "type": var[1], "def": var[2]}
                            )
                        session.commit()
                    st.success("Successfully broadcasted your study metadata layout live to the global community database!")
                    st.rerun()
                else:
                    st.error("Global database engine credentials are unconfigured or offline. Please save using 'Local Locked' mode.")

# --- STEP 3: DATA VISUALIZATION EXPLORER REGISTRIES ---
st.divider()
st.header("🔍 Explored Studies Registries")

if db_mode == "Local Locked (SQLite File)":
    conn = sqlite3.connect(st.session_state.local_db_path)
    try:
        df_studies = pd.read_sql_query("SELECT * FROM studies ORDER BY id DESC", conn)
        df_vars = pd.read_sql_query("SELECT * FROM variables", conn)
    finally:
        conn.close()
        
    # Provide local SQLite backup file downloading stream
    with open(st.session_state.local_db_path, "rb") as f:
        st.sidebar.download_button(
            label="📥 Download Local Registry (.db)",
            data=f.read(),
            file_name="open_ed_metadata_registry.db",
            mime="application/x-sqlite3"
        )
else:
    if shared_conn is not None:
        try:
            df_studies = shared_conn.query("SELECT * FROM studies ORDER BY id DESC;", ttl="0")
            df_vars = shared_conn.query("SELECT * FROM variables;", ttl="0")
        except Exception:
            df_studies, df_vars = pd.DataFrame(), pd.DataFrame()
    else:
        st.warning("Public Collaborative Database running in offline mode. Configure Streamlit Secrets to enable the global community hub.")

# Render output cards natively using interactive expanders
if not df_studies.empty:
    for idx, row in df_studies.iterrows():
        with st.expander(f"📚 {row['title']} — by {row['authors'] if row['authors'] else 'Unknown'}"):
            st.markdown(f"**Keywords:** `{row['keywords']}`")
            st.markdown(f"### Abstract\n{row['abstract'] if row['abstract'] else '*No summary provided.*'}")
            st.markdown(f"### Theoretical Framework\n{row['theoretical_framework'] if row['theoretical_framework'] else '*None specified.*'}")
            
            if not df_vars.empty:
                matched_vars = df_vars[df_vars['study_id'] == row['id']]
                if not matched_vars.empty:
                    st.markdown("### Collected Variables Layout")
                    st.dataframe(
                        matched_vars[['variable_name', 'variable_type', 'operational_definition']], 
                        use_container_width=True,
                        hide_index=True
                    )
else:
    st.info("No study models found matching your current workspace selection database filter criteria.")


