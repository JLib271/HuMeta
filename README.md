# Open Educational Metadata Platform 🔬🌐

An open-source, community-driven web app that helps STEM education researchers standardize, align, and share study and survey metadata. It runs on Streamlit Community Cloud with **no database**: private work stays with the researcher, and public records live in this GitHub repository after maintainer review.

## 🤝 Community

OpenEdMetadata is open source and welcomes contributors, from researchers adding instruments to developers.
Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the [ROADMAP.md](ROADMAP.md). We follow a [Code of Conduct](CODE_OF_CONDUCT.md);
see [GOVERNANCE.md](GOVERNANCE.md) for how decisions are made and [SECURITY.md](SECURITY.md) to report security or privacy problems.
To cite the project, use [CITATION.cff](CITATION.cff).

## 🔗 Live Application Access
The platform is deployed on Streamlit Community Cloud.
👉 **Open Educational Metadata Portal:** _link to be added — replace this line with the app's `*.streamlit.app` URL._

---

## 🛠️ Key Architectural Layout (Modules 1–6)

The modules follow a study from design to sharing. Study metadata uses one standard throughout: the [STEMEd+ Metadata Application Profile](standard/stemed-ap/README.md).

1. **Study Metadata Profile (Module 1):** Describe the study with the STEMEd+ profile: title and team (with ORCID iDs), design (topic, research questions, study design, unit of analysis, sampling, data collection), population and context, instructional setting, ethics review, consent for participation and for data sharing, identifiability and access, and Indigenous data governance (CARE). Answers use the profile's controlled vocabularies. Saving puts the record into a **project file** the researcher downloads and keeps; governance fields are researcher-reported and are not approval or sharing determinations.
2. **Variable Instrument Architect (Module 2):** Starts with **Find previously shared studies with related context**, which searches study summaries other researchers have published (study-design and variable/measurement metadata, never item text or participant data). The query is populated from the Module 1 content domain when available. Step 1 captures broad study context; a target behavior and timeframe are optional, and the app does not presume behavior is the study outcome. Step 2 uses a multi-select to choose framework variables, followed by the **Included theory-derived, demographic, and contextual variables** metadata editor, including a context-personalized TPB questionnaire example (app-generated examples, not a validated measure). Step 3 adds or imports custom variables with item text/source type, response scale, language, scoring, citation/URL, adaptation notes, and validity/reliability evidence. Step 4 builds a conceptual diagram; Step 5 reviews variables and downloads the matrices and draft survey. The plan is saved into the project file. Researchers can opt in to **submit a limited study summary for public listing**, which opens a pull request for maintainer review.
3. **Check & Export Metadata (Module 3):** Add the constructs measured (suggested from the Module 2 plan, linked to library instruments), check the record against the profile's responsible-sharing rules (consent, de-identification, review status, CARE), and export STEMEd+ JSON, DataCite 4.7 JSON/XML, and ERIC Thesaurus descriptors.
4. **Community Data Repository Sync (Module 4):** Browse and download published public datasets, or submit a de-identified dataset for public release after permission, identifier, and disclosure-risk confirmations. Submissions open a pull request and are listed only after a maintainer merges them. **Private datasets are never stored.**
5. **Descriptive & Scale Analytics (Module 5):** Upload a private dataset (held in memory for the browser session only and never saved), pick a published dataset, or use synthetic sample data; map columns to Module 2 variables; inspect distributions and descriptive statistics; review composite scores, reliability, and correlations; and download a PDF report. Numeric mappings support composite scores and Cronbach's alpha for multi-item mappings; categorical mappings show response counts.
6. **Published Repository Viewer (Module 6):** Browse the published study summaries, the public dataset catalog, and the research measure catalog, and download any of them as CSV.

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
| Private datasets | In memory for the current browser session (Module 5) | Only the researcher; discarded on reload or when the session ends |
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

## 🔐 Researcher sign-in (Google)

Every module works without signing in. Signing in is required only to submit
items for review (study summaries, public datasets, suggestions), so that each
pull request is tied to a real account. The app uses Streamlit's built-in
OpenID Connect sign-in with Google, so any Google account works, including
university Google Workspace accounts. Pull requests show the submitter's display
name and a short hashed account reference, never their email address.

To set it up (about 10 minutes, free):

1. In [Google Cloud Console](https://console.cloud.google.com/), create a
   project, then open **APIs & Services → OAuth consent screen**. Choose
   **External**, fill in the app name and support email, and keep only the
   basic `openid`, `email`, and `profile` scopes.
2. Under **Audience**, click **Publish app** so it is "In production".
   (In "Testing" mode only the test users you list can sign in.) Apps that use
   only the basic scopes don't need Google's verification review.
3. Open **Credentials → Create credentials → OAuth client ID**, choose
   **Web application**, and add the authorized redirect URI
   `https://<your-app>.streamlit.app/oauth2callback`
   (add `http://localhost:8501/oauth2callback` too for local testing).
4. Copy the client ID and secret into the app's secrets (below). Without an
   `[auth]` section the app still runs; only submissions are disabled.

The code uses whichever OpenID Connect provider is in `[auth]`, so switching
later (for example to CILogon or Microsoft) only needs new secrets and a new
button label.

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
client_id = "xxxxxxxx.apps.googleusercontent.com"
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

For local development, put the same content in `.streamlit/secrets.toml`
(already git-ignored) and use `http://localhost:8501/oauth2callback` as the
redirect URI (it must also be listed in the Google OAuth client).

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

5. **Run the tests** (the same checks run on every pull request):
   ```bash
   pip install -r requirements-dev.txt
   python -m pytest -v                 # unit tests + opens every app page headlessly
   python scripts/validate_library.py  # instrument library checks
   ruff check --select F,E9 openscience.py oem tests scripts
   ```

---

## 🧭 Project Structure

```text
openscience.py            Streamlit entry point: page config, sidebar, router
oem/                      Core logic with no Streamlit dependency
  library.py              Load instruments, items, constructs, scales, standard variables
  naming.py               Shared variable-naming rules
  codebook.py             Build and export codebooks (CSV / JSON)
  profile.py              STEMEd+ profile: records, validation, DataCite and ERIC exports
  vocab.py                Controlled vocabularies used by the forms
  app/common.py           Streamlit helpers shared by all pages
  app/pages/              One file per module, each with render()
library/                  Instrument library (CC BY-SA 4.0 content; see library/README.md)
standard/stemed-ap/       STEMEd+ Metadata Application Profile: spec, vocabularies, crosswalks
tests/                    pytest suite, including an app smoke test
scripts/validate_library.py   Library validator (also runs in CI)
published/, suggestions/  Reviewed public records submitted through the app
```

New logic should go in `oem/` with tests in `tests/`; pages should stay thin and
call into it. See [CONTRIBUTING.md](CONTRIBUTING.md).

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

Module 5 shows example analysis code that uses `scipy` and `statsmodels`;
researchers install those in their own analysis environment. The portal itself
does not need them.

---

## 📄 License & Terms
The application code is licensed under the **GNU Affero General Public License, version 3 or (at your option) any later version** (AGPL-3.0-or-later); see [`LICENSE`](LICENSE). Other research institutions and education task forces are welcome to copy, modify, run, and redistribute this platform. If you distribute a modified version, or run a modified version as a service that others use over a network, you must make your modified source code available to its users under the same license.

Copyright (C) 2026 Julie C. Libarkin. Versions released before this change remain available under the MIT License.

The instrument library in `library/` is licensed separately: records are CC BY-SA 4.0, and each instrument's item text carries its own license. See [`library/LICENSE.md`](library/LICENSE.md).
