# Open Educational Metadata Platform 🔬🌐

An open-source, community-driven web app that helps STEM education researchers standardize, align, and share study and survey metadata. It runs on Streamlit Community Cloud with **no database**: private work stays with the researcher, and public records live in this GitHub repository after maintainer review.

## 🔗 Live Application Access
The platform is deployed on Streamlit Community Cloud.
👉 **Open Educational Metadata Portal:** _link to be added — replace this line with the app's `*.streamlit.app` URL._

---

## 🛠️ Key Architectural Layout (Modules 1–5)

The system is split into five core functional layers managed by interactive sidebar navigation:

1. **Study Metadata Schema Registry (Module 1):** Capture study identity, team, research questions, design, population, one open-text content domain or topic, ethics-review context, permissions, and data-sharing plans. Population and setting options include schools and learners as well as the general public, community members, museum and science-center visitors, families, and public events. Governance fields are researcher-reported and are not approval or sharing determinations. Saving puts the study into a **project file** the researcher downloads and keeps.
2. **Variable Instrument Architect (Module 2):** Starts with **Find previously shared studies with related context**, which searches study summaries other researchers have published (study-design and variable/measurement metadata, never item text or participant data). The query is populated from the Module 1 content domain when available. Step 1 captures broad study context; a target behavior and timeframe are optional, and the app does not presume behavior is the study outcome. Step 2 uses a multi-select to choose framework variables, followed by the **Included theory-derived, demographic, and contextual variables** metadata editor, including a context-personalized TPB questionnaire example (app-generated examples, not a validated measure). Step 3 adds or imports custom variables with item text/source type, response scale, language, scoring, citation/URL, adaptation notes, and validity/reliability evidence. Step 4 builds a conceptual diagram; Step 5 reviews variables and downloads the matrices and draft survey. The plan is saved into the project file. Researchers can opt in to **submit a limited study summary for public listing**, which opens a pull request for maintainer review.
3. **Community Data Repository Sync (Module 3):** Browse and download published public datasets, or submit a de-identified dataset for public release after permission, identifier, and disclosure-risk confirmations. Submissions open a pull request and are listed only after a maintainer merges them. **Private datasets are never stored.**
4. **Descriptive & Scale Analytics (Module 4):** Upload a private dataset (held in memory for the browser session only and never saved), pick a published dataset, or use synthetic sample data; map columns to Module 2 variables; inspect distributions and descriptive statistics; review composite scores, reliability, and correlations; and download a PDF report. Numeric mappings support composite scores and Cronbach's alpha for multi-item mappings; categorical mappings show response counts.
5. **Published Repository Viewer (Module 5):** Browse the published study summaries, the public dataset catalog, and the research measure catalog, and download any of them as CSV.

### Research measure catalog

Module 2 reads the versioned JSON catalog at
[`catalogs/measure_catalog.json`](catalogs/measure_catalog.json). Add one
reviewed instrument record per measure, using the field definitions and example
in [`catalogs/README.md`](catalogs/README.md). Module 2 matches catalog entries
to included variables, selected frameworks, and saved Module 1 subject areas,
then shows descriptions, evidence, citations, and license/terms for researcher
review. Keep the catalog empty until entries have verified sources; the app
does not establish instrument validity or permissions.

To add or revise catalog entries, edit the JSON file, validate it locally by
opening Module 2, then commit and push the catalog change with the app code.
No secrets setup is needed; deployments read the catalog file from the same
repository revision as `openscience.py`.

---

## 🤖 Community Theory and Variable Suggestions
Signed-in researchers can submit, from Module 2, a theory and variable map, literature rationale,
and conceptual relationships as a JSON file in `suggestions/`, on a new branch
with a pull request to `main`. Maintainers review and merge accepted suggestions;
submissions do not update the app's built-in catalog automatically. Contributors
must confirm that their submission contains no confidential or identifying
information. Pull requests are public, so do not include participant information,
private study details, unpublished results, or other sensitive content.

Configure `GITHUB_PAT` as a fine-grained token limited to this repository, with
Contents: Read and write and Pull requests: Read and write permissions. The token
is stored only in the Streamlit app's secrets and is not shown to researchers.
The app can only write to `suggestions/`, `published/study_summaries/`, and
`published/datasets/`, and only on new branches. Because the token itself could
push to `main`, also turn on a branch protection rule (or ruleset) for `main`
that requires a pull request before merging, so nothing reaches `main` without a
maintainer's approval.
GitHub organization policies may require an administrator to approve the token.

---

## 🗂️ Where data lives (no database)

| Data | Where it lives | Who can see it |
| --- | --- | --- |
| Study record (Module 1) and Module 2 plan | A project file (`*.oem-project.json`) the researcher downloads and re-opens from the sidebar | Only the researcher — the app keeps no copy |
| Private datasets | In memory for the current browser session (Module 4) | Only the researcher; discarded on reload or when the session ends |
| Published study summaries | `published/study_summaries/` in this repo | Everyone, after a maintainer merges the pull request |
| Published datasets | `published/datasets/` in this repo (CSV + JSON metadata, up to 25 MB) | Everyone, after a maintainer merges the pull request |
| Theory / variable / analytics suggestions | `suggestions/` in this repo | Everyone, after a maintainer merges the pull request |
| Research measure catalog | `catalogs/measure_catalog.json` | Everyone |

Researchers should keep project files in storage approved for their study
(for example, their institution's managed drive), since the file can contain
unpublished study details. See [`published/README.md`](published/README.md) for
the maintainer review checklist. Anything merged into `published/` is public and
remains in git history even if it is later removed.

---

## 🔐 Researcher sign-in (CILogon)

Every module works without signing in. Signing in is required only to submit
items for review (study summaries, public datasets, suggestions), so that each
pull request is tied to a verified researcher. The app uses Streamlit's built-in
OpenID Connect sign-in with [CILogon](https://www.cilogon.org/oidc), the same
federated institutional login used by STEMEd+ Commons / Knowledge Commons.

Pull requests show the submitter's display name and a short hashed account
reference — never their email address. The app asks for the standard
`openid profile email` scopes.

To set it up:

1. Register an OIDC client with CILogon (<https://cilogon.org/oauth2/register>),
   or ask the STEMEd+ Commons / Knowledge Commons administrators whether to
   register through their CILogon COmanage registry instead. Use the callback
   URL `https://<your-app>.streamlit.app/oauth2callback` and request the
   `openid`, `email`, and `profile` scopes. CILogon administrators must approve
   the client before it works.
2. Add the client to the app's secrets (below). Without an `[auth]` section the
   app still runs; only submissions are disabled.

---

## ⚙️ Secrets Deployment Configuration

In Streamlit Community Cloud, open the app's **Settings → Secrets** and add:

```toml
# Fine-grained GitHub token limited to this repository:
# Contents: Read and write; Pull requests: Read and write
GITHUB_PAT = "your-fine-grained-token"
# Optional; defaults to JLib271/OpenEdMetadata
GITHUB_REPO = "JLib271/OpenEdMetadata"

[auth]
redirect_uri = "https://<your-app>.streamlit.app/oauth2callback"
cookie_secret = "a-long-random-string"   # e.g. python -c "import secrets; print(secrets.token_urlsafe(32))"
client_id = "cilogon:/client_id/..."
client_secret = "..."
server_metadata_url = "https://cilogon.org/.well-known/openid-configuration"
```

For local development, put the same content in `.streamlit/secrets.toml`
(already git-ignored) and use `http://localhost:8501/oauth2callback` as the
redirect URI (it must also be registered with CILogon).

Supabase is no longer used: remove `SUPABASE_URL`, `SUPABASE_KEY`, and
`APP_URL` from existing deployments' secrets.

---

## 🚀 Local Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/JLib271/OpenEdMetadata.git
   cd OpenEdMetadata
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Optional — configure secrets** in `.streamlit/secrets.toml` (see above) if
   you want to test sign-in and pull-request submissions.

4. **Launch the app:**
   ```bash
   streamlit run openscience.py
   ```

---

## 📜 Dependencies Checklist (`requirements.txt`)
```text
streamlit>=1.42.0
Authlib>=1.3.2
streamlit-flow-component>=1.6.1,<2.0.0
pandas>=2.0.0
numpy>=1.24.0
PyGithub>=2.1.0
matplotlib>=3.7.0
reportlab>=4.0.0
```

Module 4 shows example analysis code that uses `scipy` and `statsmodels`;
researchers install those in their own analysis environment. The portal itself
does not need them.

---

## 📄 License & Terms
Distributed under the **MIT License**. Other research institutions and education task forces are explicitly granted legal permission to copy, alter, scale, and redistribute this platform, provided proper attribution credit is maintained.
