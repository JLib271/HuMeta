# HuMeta Portal 🔬🌐

An open-source, community-driven web app that helps researchers in the **social sciences, humanities, and education** describe, align, and share study metadata using one open standard, **HuMeta: The Social Science, Humanities, and Education Study Metadata Profile**. It runs on Streamlit Community Cloud with **no database**: private work stays with the researcher, and public records live in this GitHub repository after maintainer review.

## 🤝 Community

The project is open source and welcomes contributors: researchers drafting field modules or adding instruments, librarians and data curators, and developers.
Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the [ROADMAP.md](ROADMAP.md). We follow a [Code of Conduct](CODE_OF_CONDUCT.md);
see [GOVERNANCE.md](GOVERNANCE.md) for how decisions are made and [SECURITY.md](SECURITY.md) to report security or privacy problems.
To cite the project, use [CITATION.cff](CITATION.cff).

## 🔗 Live Application Access
The platform is deployed on Streamlit Community Cloud.
👉 **HuMeta Portal:** _link to be added — replace this line with the app's `*.streamlit.app` URL._

---

## 🛠️ Key Architectural Layout (Modules 1–6)

The modules follow a study from design to sharing. Study metadata uses one standard throughout: the [HuMeta profile](standard/humeta/README.md). It has a core for every study plus optional field modules for Education, Social Science, and Arts and Humanities, each a starting point to be developed with researchers in those fields. The Social Science module uses DDI, the field's existing standard, and links to a study's full DDI documentation rather than recreating it.

1. **Study Metadata Profile (Module 1):** Start by choosing the study's fields (Education, Social science, Arts and humanities), which adds a short section for each. Then describe the study with the HuMeta profile: title and team (with ORCID iDs), research fields and disciplines, design (topic, research questions, study design, unit of analysis, sampling, data collection and analysis methods), people and place (including studies with no participants), sources (texts, archives, images, artworks, media, online content, objects), the field sections (Education: education level, institution type, instructional setting; Social science: kind of data, universe, geographic unit, response rate, weighting, and a link to the study's DDI documentation; Arts and humanities: TaDiRAH research activities, works or objects studied, languages of the sources, editorial or encoding standards), ethics review, consent for participation and for data sharing, identifiability and access, practices for public online data, and Indigenous data governance (CARE). Answers use the profile's controlled vocabularies. Saving puts the study profile into a **project file** the researcher downloads and keeps; governance fields are researcher-reported and are not approval or sharing determinations.
2. **Framework and Measures (Module 2):** Theory organizes the module. (1) Choose the framework that guides the study: a theory (e.g., Self-Determination Theory, Expectancy-Value Theory, Theory of Planned Behavior), a theoretical lens (e.g., sociocultural theory, critical race theory, feminist theory), your own conceptual framework, or an exploratory/inductive approach. (2) The framework supplies its constructs, optionally linked to the shared construct list; keep the ones your study addresses and add your own. (3) Give each construct a measure: a library instrument or subscale (shown as candidates with their mapping status; the researcher decides whether one fits, and a governance committee will decide which instruments map to which constructs), researcher-written questions, or codes in a coding scheme for texts, images, media, or interviews. (4) The framework's expected relationships draw the diagram, which you can edit. (5) Review the generated codebook (shared variable names), add standard variables and timepoints, and save the **variable plan** to the project file. The framework is also recorded in the study profile. Downloads: codebook (CSV/JSON), variable matrix for Module 5, and the diagram. Researchers can opt in to publish a limited study summary. Module 2's **Recommend** tabs are the place to recommend theories, conceptual models, frameworks, and instruments (with an explicit table of what each part of an instrument measures), or to suggest corrections. Each opens a reviewed pull request that adds a structured file to `suggestions/`, and no GitHub account is needed.
3. **Check & Export Metadata (Module 3):** Add the constructs measured (suggested from the variable plan in Module 2, linked to library instruments), check the study profile against the profile's responsible-sharing rules (consent, de-identification, review status, CARE), and export HuMeta JSON, DataCite 4.7 JSON/XML, ERIC Thesaurus descriptors, and **DDI-Codebook 2.5** XML for social science archives (ICPSR, CESSDA, the UK Data Service, Dataverse). The DDI file describes the study and, when a Module 2 variable plan is saved, every variable: label, question text, codes and missing codes, grouped by construct, with each variable naming the construct it measures. It validates against the official DDI-Codebook 2.5.1 schema.
4. **Community Data Repository Sync (Module 4):** Browse and download published public datasets, or submit a de-identified dataset for public release after permission, identifier, and disclosure-risk confirmations. Submissions open a pull request and are listed only after a maintainer merges them. **Private datasets are never stored.**
5. **Descriptive & Scale Analytics (Module 5):** Analyze data by construct, using the variable plan from Module 2. Upload a private dataset (held in memory for the browser session only and never saved), pick a published dataset, or try example data shaped like your plan. Columns are matched to the plan by their shared variable names (adjustable); without a plan you define scales by hand. For each construct and measure, and each timepoint: descriptives, a scale score (mean or sum), and Cronbach's alpha with a 95% confidence interval, corrected item-total correlations, and alpha if item deleted; codes show how often each is present. Then relationships and comparisons: correlations of scale scores (n, r, 95% CI, p); group comparisons (Welch's t-test and Mann-Whitney U for two groups; ANOVA, Welch's ANOVA, Kruskal-Wallis, and Games-Howell follow-ups for three or more); before-and-after comparisons (paired t-test and Wilcoxon signed-rank, with pre/post pairs suggested from the plan's timepoints); chi-square tests of association with Cramér's V; and linear or logistic regression with confidence intervals (and odds ratios). Each test reports an effect size and a plain-language summary. Statistics are computed with [pingouin](https://pingouin-stats.org/) (Vallat, 2018). Downloads: scale scores, results tables, a PDF report, and an R script (psych and base R) that reproduces the analyses, including McDonald's omega and the tests chosen, on the researcher's own computer. Links point to other free tools (R, psych, lavaan, JASP, jamovi), and researchers can recommend analyses for the module.
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
| Study profile (Module 1) and variable plan (Module 2) | A project file (`*.humeta-project.json`) the researcher downloads and re-opens from the sidebar | Only the researcher — the app keeps no copy |
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
# Contents: Read and write; Pull requests: Read and write; Issues: Read and write (for the feedback box)
GITHUB_PAT = "your-fine-grained-token"
# Optional; defaults to JLib271/HuMeta
GITHUB_REPO = "JLib271/HuMeta"
# Optional: require Google sign-in to send feedback (recommended once the app is public)
# FEEDBACK_REQUIRES_SIGN_IN = true

[auth]
redirect_uri = "https://<your-app>.streamlit.app/oauth2callback"
cookie_secret = "a-long-random-string"   # e.g. python -c "import secrets; print(secrets.token_urlsafe(32))"
client_id = "xxxxxxxx.apps.googleusercontent.com"
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

### Sharing the app with testers

1. Deploy on Streamlit Community Cloud from this repository (main file `openscience.py`) and add the secrets above.
2. While the repository is private, the app is private too. Invite testers from the app's **Share** button by
   email; they sign in with Google or a one-time emailed link. No GitHub account is needed.
3. Testers use **Send feedback about this page** at the bottom of any page. Each message becomes a GitHub
   issue labeled `feedback`, with its kind (`feedback: confusing`, `feedback: bug`, …) and page
   (`page: module 2`, …). See them all at
   [issues labeled feedback](https://github.com/JLib271/HuMeta/issues?q=label%3Afeedback).

For local development, put the same content in `.streamlit/secrets.toml`
(already git-ignored) and use `http://localhost:8501/oauth2callback` as the
redirect URI (it must also be listed in the Google OAuth client).

Supabase is no longer used: remove `SUPABASE_URL`, `SUPABASE_KEY`, and
`APP_URL` from existing deployments' secrets.

---

## 🚀 Local Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/JLib271/HuMeta.git
   cd HuMeta
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
  profile.py              HuMeta profile: records, validation, DataCite and ERIC exports
  vocab.py                Controlled vocabularies used by the forms
  app/common.py           Streamlit helpers shared by all pages
  app/pages/              One file per module, each with render()
library/                  Instrument library (CC BY-SA 4.0 content; see library/README.md)
standard/humeta/             HuMeta profile: spec, vocabularies, crosswalks
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
pandas>=2.0.0
numpy>=1.24.0
PyGithub>=2.1.0
matplotlib>=3.7.0
reportlab>=4.0.0
pingouin>=0.5.4
```

Module 5's statistics use `pingouin` (installed from `requirements.txt`). The
downloadable R script needs R with the `psych` package on the researcher's own
computer; the portal itself does not need R.

---

## 📄 License & Terms
The application code is licensed under the **GNU Affero General Public License, version 3 or (at your option) any later version** (AGPL-3.0-or-later); see [`LICENSE`](LICENSE). Other research institutions and education task forces are welcome to copy, modify, run, and redistribute this platform. If you distribute a modified version, or run a modified version as a service that others use over a network, you must make your modified source code available to its users under the same license.

Copyright (C) 2026 Julie C. Libarkin. Versions released before this change remain available under the MIT License.

The instrument library in `library/` is licensed separately: records are CC BY-SA 4.0, and each instrument's item text carries its own license. See [`library/LICENSE.md`](library/LICENSE.md).
