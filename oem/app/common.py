# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Streamlit helpers shared by every page: sign-in, project files, published
records, the measure catalog, review pull requests, and module cards."""

from __future__ import annotations
import streamlit as st
import json
import os
import re
import hashlib
import time
import uuid
from pathlib import Path
from github import Github
from oem.vocab import (APP_DIR, DEFAULT_GITHUB_REPO, PROJECT_FILE_FORMAT, PUBLISHED_DATASETS_DIR, PUBLISHED_SUMMARIES_DIR, THEORY_CITATIONS)


# Storage model (no database):
# - Private study records and Module 2 plans live only in a project file the
#   researcher downloads and re-opens; the app never stores them.
# - Private datasets are analyzed in memory for the current session only.
# - Public study summaries and datasets live in this GitHub repository under
#   published/. Researchers submit them as pull requests; they become public
#   only after a maintainer merges, and the deployed app reads them from disk.

def auth_is_configured() -> bool:
    """True when an [auth] section (Google OpenID Connect) exists in secrets."""
    try:
        return "auth" in st.secrets
    except Exception:
        return False


def researcher_is_signed_in() -> bool:
    return auth_is_configured() and bool(getattr(st.user, "is_logged_in", False))


def researcher_display_name() -> str:
    name = str(st.user.get("name") or "").strip() if researcher_is_signed_in() else ""
    return name or "Signed-in researcher"


def researcher_reference() -> str:
    """Stable, non-identifying reference for a signed-in researcher.

    The OIDC subject is hashed so pull requests can be traced to an account
    without publishing an email address or raw identifier.
    """
    if not researcher_is_signed_in():
        return ""
    subject = str(st.user.get("sub") or st.user.get("email") or "")
    return hashlib.sha256(subject.encode("utf-8")).hexdigest()[:12] if subject else ""


# ---------- Researcher-kept project files ----------

def empty_project() -> dict:
    return {
        "format": PROJECT_FILE_FORMAT,
        "schema_version": 1,
        "study": None,
        "module2_plan": {},
        "profile_record": None,
    }


def current_project() -> dict:
    if "project" not in st.session_state:
        st.session_state["project"] = empty_project()
    return st.session_state["project"]


def parse_project_file(raw_bytes: bytes) -> dict:
    project = json.loads(raw_bytes.decode("utf-8"))
    if not isinstance(project, dict) or project.get("format") != PROJECT_FILE_FORMAT:
        raise ValueError("This is not a HuMeta Portal project file.")
    study = project.get("study")
    if study is not None and (not isinstance(study, dict) or not study.get("id")):
        raise ValueError("The project file's study record is missing or malformed.")
    plan = project.get("module2_plan") or {}
    if not isinstance(plan, dict):
        raise ValueError("The project file's Module 2 plan is malformed.")
    profile_record = project.get("profile_record")
    if profile_record is not None and not isinstance(profile_record, dict):
        raise ValueError("The project file's HuMeta metadata record is malformed.")
    loaded = empty_project()
    loaded.update({"study": study, "module2_plan": plan, "profile_record": profile_record})
    return loaded


def project_file_bytes() -> bytes:
    project = dict(current_project())
    project["saved_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return json.dumps(project, ensure_ascii=False, indent=2).encode("utf-8")


def project_file_name() -> str:
    study = current_project().get("study") or {}
    slug = re.sub(r"[^a-z0-9]+", "_", str(study.get("study_title") or "study").lower()).strip("_")
    return f"{(slug or 'study')[:60]}.oem-project.json"


def render_project_download(key: str, label: str = "Download project file") -> None:
    st.download_button(
        label,
        data=project_file_bytes(),
        file_name=project_file_name(),
        mime="application/json",
        key=key,
        use_container_width=True,
        help="Keep this file somewhere safe (e.g., your institution's storage). "
        "The app does not keep a copy; open it again from the sidebar to continue.",
    )


# ---------- Published (public) records in this repository ----------

def _read_json_files(folder: Path) -> list[dict]:
    records = []
    if not folder.is_dir():
        return records
    for path in sorted(folder.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(record, dict):
            record["_file"] = path.name
            records.append(record)
    return records


@st.cache_data(ttl=300, show_spinner=False)
def load_published_summaries() -> list[dict]:
    return _read_json_files(PUBLISHED_SUMMARIES_DIR)


@st.cache_data(ttl=300, show_spinner=False)
def load_published_datasets() -> list[dict]:
    datasets = []
    for record in _read_json_files(PUBLISHED_DATASETS_DIR):
        csv_name = os.path.basename(str(record.get("csv_file") or ""))
        csv_path = PUBLISHED_DATASETS_DIR / csv_name
        if csv_name.endswith(".csv") and csv_path.is_file():
            record["_csv_path"] = str(csv_path)
            datasets.append(record)
    return datasets


def safe_slug(value: str, fallback: str = "item", max_length: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return (slug or fallback)[:max_length].strip("-") or fallback


def context_search_terms(value: str) -> list[str]:
    stop_words = {
        "about", "after", "among", "and", "are", "for", "from", "into",
        "its", "our", "that", "the", "their", "this", "through", "with",
    }
    return list(dict.fromkeys(
        token
        for token in "".join(
            character.lower() if character.isalnum() else " "
            for character in str(value)
        ).split()
        if len(token) > 2 and token not in stop_words
    ))



def citation_for_framework(framework: str) -> str:
    return THEORY_CITATIONS.get(
        framework,
        "No primary citation for this framework is listed in the linked source; add a citation.",
    )


MEASURE_CATALOG_PATH = APP_DIR / "catalogs" / "measure_catalog.json"
MEASURE_CATALOG_REQUIRED_FIELDS = {
    "measure_id",
    "discipline",
    "study_area",
    "variable",
    "theory_framework",
    "measure_name",
    "population_context",
    "response_format",
    "scoring",
    "validity_evidence",
    "reliability_evidence",
    "citation",
    "doi_url",
    "source_url",
    "license",
    "notes",
}


def load_measure_catalog() -> list[dict]:
    with MEASURE_CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)
    if not isinstance(catalog, dict) or not isinstance(catalog.get("measures"), list):
        raise ValueError("Catalog must be a JSON object containing a 'measures' list.")
    if catalog.get("catalog_version") != 1:
        raise ValueError("Unsupported measure catalog version.")
    for index, measure in enumerate(catalog["measures"]):
        if not isinstance(measure, dict):
            raise ValueError(f"Catalog entry {index + 1} must be a JSON object.")
        missing_fields = MEASURE_CATALOG_REQUIRED_FIELDS - measure.keys()
        if missing_fields:
            raise ValueError(
                f"Catalog entry {index + 1} is missing fields: "
                f"{', '.join(sorted(missing_fields))}."
            )
    return catalog["measures"]


def find_measure_suggestions(
    catalog: list[dict],
    variable: str,
    frameworks: list[str],
    study_areas: list[str],
) -> list[dict]:
    variable_key = variable.strip().casefold()
    framework_keys = {value.strip().casefold() for value in frameworks if value.strip()}
    study_area_keys = {value.strip().casefold() for value in study_areas if value.strip()}
    matches = []
    for measure in catalog:
        catalog_variable = str(measure["variable"]).strip().casefold()
        if catalog_variable not in {"", "*", variable_key}:
            continue
        catalog_frameworks = measure["theory_framework"]
        if isinstance(catalog_frameworks, str):
            catalog_frameworks = [catalog_frameworks] if catalog_frameworks else []
        catalog_framework_keys = {
            str(value).strip().casefold()
            for value in catalog_frameworks
            if str(value).strip()
        }
        if framework_keys and catalog_framework_keys and not framework_keys.intersection(catalog_framework_keys):
            continue
        catalog_disciplines = measure["discipline"]
        if isinstance(catalog_disciplines, str):
            catalog_disciplines = [catalog_disciplines] if catalog_disciplines else []
        catalog_discipline_keys = {
            str(value).strip().casefold()
            for value in catalog_disciplines
            if str(value).strip()
        }
        if study_area_keys and catalog_discipline_keys and not study_area_keys.intersection(catalog_discipline_keys):
            continue
        catalog_areas = measure["study_area"]
        if isinstance(catalog_areas, str):
            catalog_areas = [catalog_areas] if catalog_areas else []
        catalog_area_keys = {
            str(value).strip().casefold()
            for value in catalog_areas
            if str(value).strip()
        }
        if study_area_keys and catalog_area_keys and not study_area_keys.intersection(catalog_area_keys):
            continue
        matches.append(measure)
    return matches


value_propositions = [
    (
        "1. Study Metadata Profile",
        "📐 One Shared Metadata Standard",
        "Describes every study with HuMeta, the Social Science, Humanities, and Education Study Metadata Profile, so studies across "
        "institutions use the same fields and vocabularies and stay searchable and comparable.",
        "1. Study Metadata Profile",
        [
            "Describe the study, team, design, population, and instructional setting.",
            "Record ethics review, consent for participation and for data sharing, and access plans.",
            "Address Indigenous data governance (CARE) where it applies.",
            "Save it to a project file you keep — the app stores nothing private.",
        ],
    ),
    (
        "2. Variable Instrument Architect",
        "🗺️ Theoretical-to-Variable Mapping",
        "Directly assists researchers in building out robust study designs derived from "
        "conceptual frameworks seamlessly linked to operational variables.",
        "2. Variable Instrument Architect",
        [
            "Find related study summaries shared by other researchers.",
            "Select frameworks and variables; define measurement and questionnaire metadata.",
            "Build a conceptual diagram and download variable matrices and a draft survey.",
        ],
    ),
    (
        "3. Check & Export Metadata",
        "🏷️ Standards-Ready Metadata",
        "Completes the HuMeta record with the constructs you measure, checks it against the profile's "
        "responsible-sharing rules, and exports metadata that DOI registration and education indexes use.",
        "3. Check & Export Metadata",
        [
            "Add constructs measured, suggested from your Module 2 plan.",
            "See what to fix before sharing: consent, de-identification, review, CARE.",
            "Export HuMeta JSON, DataCite 4.7 (JSON/XML), and ERIC descriptors.",
        ],
    ),
    (
        "4. Community Data Repository Sync",
        "🌍 Global Open-Data Ingestion",
        "Bridges individual datasets directly onto a unified global sharing infrastructure "
        "for frictionless, public-facing discovery.",
        "4. Community Data Repository Sync",
        [
            "Browse and download datasets researchers have published.",
            "Review permissions, identifiers, and disclosure risks before public release.",
            "Submit a de-identified dataset for maintainer review (private data is never stored).",
        ],
    ),
    (
        "5. Descriptive & Scale Analytics",
        "📊 Comparative Meta-Analytics",
        "Maps observed dataset columns to the theory-derived, demographic/contextual, and custom "
        "variables defined in Module 2, then supports descriptive, composite-score, reliability, "
        "and relationship analyses.",
        "5. Descriptive & Scale Analytics",
        [
            "Upload a private dataset (kept in memory only) or pick a published one, then map its columns to Module 2 variables.",
            "Inspect distributions, descriptive statistics, and categorical responses.",
            "Review composite scores, reliability, correlations, and download a report.",
        ],
    ),
    (
        "6. Published Repository Viewer",
        "🧪 Open Published Registry",
        "Shows the reviewed, publicly shared study summaries, dataset catalog, and research "
        "measure catalog maintained in the project's GitHub repository.",
        "6. Published Repository Viewer",
        [
            "Choose published study summaries, datasets, or measures.",
            "Browse the reviewed public records.",
            "Download the displayed table as CSV.",
        ],
    ),
]

ALLOWED_PR_FOLDERS = ("suggestions/", "published/study_summaries/", "published/datasets/")


def open_review_pull_request(
    suggestion_type: str,
    title_summary: str,
    files: dict[str, str | bytes] | None = None,
    delete_paths: list[str] | None = None,
    description: str = "",
) -> str:
    """Open a pull request that maintainers must review before anything is public.

    ``files`` maps repository paths to content. Paths are restricted to the
    folders in ALLOWED_PR_FOLDERS and their file names are sanitized, so
    researcher-entered text cannot write elsewhere in the repository.
    """
    try:
        if not researcher_is_signed_in():
            return "❌ Sign in with Google before submitting items for review."
        if "GITHUB_PAT" not in st.secrets:
            return "❌ Missing 'GITHUB_PAT' in the app's secrets."

        def checked_path(path: str) -> str:
            folder, _, name = str(path).rpartition("/")
            folder = f"{folder}/"
            safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", os.path.basename(name)).strip("._")
            if folder not in ALLOWED_PR_FOLDERS or not safe_name:
                raise ValueError(f"Refusing to write outside the allowed folders: {path}")
            return folder + safe_name

        files = {checked_path(path): content for path, content in (files or {}).items()}
        delete_paths = [checked_path(path) for path in (delete_paths or [])]
        if not files and not delete_paths:
            return "❌ Nothing to submit."

        repo = Github(str(st.secrets["GITHUB_PAT"]).strip()).get_repo(
            str(st.secrets.get("GITHUB_REPO", DEFAULT_GITHUB_REPO)).strip()
        )
        base_branch = repo.default_branch
        unique_timestamp = int(time.time())
        new_branch_name = (
            f"proposal-{safe_slug(suggestion_type, 'item', 20)}-"
            f"{unique_timestamp}-{uuid.uuid4().hex[:8]}"
        )
        repo.create_git_ref(
            ref=f"refs/heads/{new_branch_name}",
            sha=repo.get_branch(base_branch).commit.sha,
        )
        commit_message = f"{suggestion_type}: {title_summary}"[:200]
        for path, content in files.items():
            repo.create_file(path=path, message=commit_message, content=content, branch=new_branch_name)
        for path in delete_paths:
            existing = repo.get_contents(path, ref=new_branch_name)
            repo.delete_file(path, f"Remove {path}", existing.sha, branch=new_branch_name)

        changed = "\n".join(f"- Add/update `{path}`" for path in files)
        removed = "\n".join(f"- Remove `{path}`" for path in delete_paths)
        pr_body = (
            "### Community submission for maintainer review\n\n"
            f"* **Type:** {suggestion_type}\n"
            f"* **Submitted by:** {researcher_display_name()} "
            f"(account ref `{researcher_reference()}`)\n\n"
            f"{description}\n\n"
            f"**Files**\n{changed}\n{removed}\n\n"
            "Before merging, check that nothing identifies participants and that the "
            "submitter's confirmations are plausible. Merged content is public and stays "
            "in git history even if later removed."
        )
        pull_request = repo.create_pull(
            title=f"[{suggestion_type}] {title_summary}"[:250],
            body=pr_body,
            head=new_branch_name,
            base=base_branch,
        )
        return (
            "🎉 Submitted for review. It becomes public only after a maintainer merges it. "
            f"Track it here: {pull_request.html_url}"
        )
    except Exception as git_error:
        return f"❌ Could not open the pull request: {git_error}"


def automate_github_pull_request(suggestion_type: str, file_name: str, file_content: str, title_summary: str) -> str:
    """Submit a suggestion file into suggestions/ as a pull request."""
    # File names are built from researcher-typed titles; flatten any "/" so the
    # file always lands directly in suggestions/.
    flat_name = re.sub(r"[^A-Za-z0-9_.-]", "_", str(file_name)).strip("._")
    return open_review_pull_request(
        suggestion_type=f"{suggestion_type} Proposal",
        title_summary=title_summary,
        files={f"suggestions/{flat_name or uuid.uuid4().hex[:12]}": file_content},
    )


def navigate_to_module(module: str) -> None:
    st.session_state["app_mode"] = module


def render_value_card(
    card: tuple[str, str, str, str, list[str]],
    show_open_button: bool = False,
) -> None:
    module_title, solution_title, description, module, actions = card
    with st.container(border=True):
        card_label, card_content = st.columns([1.4, 3.6], vertical_alignment="center")
        with card_label:
            if st.session_state.get("app_mode") == module:
                st.success("Current module")
                st.markdown(f"### {module_title}")
            else:
                st.markdown(f"#### {module_title}")
        with card_content:
            st.markdown(f"**{solution_title}**")
            st.markdown(description)
            st.markdown("**What you'll do in this module:**")
            st.markdown("\n".join(f"- {action}" for action in actions))
            if show_open_button:
                st.button(
                    f"Open {module_title}",
                    key=f"open_{module.replace(' ', '_').replace('.', '')}",
                    on_click=navigate_to_module,
                    args=(module,),
                    type="primary"
                )
