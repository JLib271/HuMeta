# Open Educational Metadata Platform 🔬🌐

An advanced, open-source, community-driven web interface and psychometric validation engine designed to standardize, align, and process educational survey data. This ecosystem is fully integrated with a live Postgres database and programmatic GitOps deployment pipelines, turning research tracking into a seamless cloud experience.

## 🔗 Live Application Access
The platform is fully compiled and deployed in a live cloud container:
👉 **[Open Educational Metadata Portal](https://streamlit.app)**

---

## 🛠️ Key Architectural Layout (Modules 1–5)

The system is split into five core functional layers managed by interactive sidebar navigation:

1. **Study Metadata Schema Registry (Module 1):** Capture study identity, team, research questions, design, population, one open-text content domain or topic, ethics-review context, permissions, and data-sharing plans. Population and setting options include schools and learners as well as the general public, community members, museum and science-center visitors, families, and public events. Governance fields are researcher-reported and are not approval or sharing determinations.
2. **Variable Instrument Architect (Module 2):** Starts with **Find previously shared studies with related context**. The query is automatically populated from the Module 1 content domain when available; signed-in researchers can edit it, search opted-in study summaries, and review shared study-design and variable/measurement metadata (not item text or participant data). Researchers explicitly opt in when saving a Module 2 plan to publish a limited summary for discovery. Step 1 uses the Module 1 content domain and captures broad study context; a target behavior and timeframe are optional, and the app does not presume behavior is the study outcome. Step 2 uses a multi-select (not a table) to choose framework variables, followed by the **Included theory-derived, demographic, and contextual variables** metadata editor. It includes a context-personalized TPB questionnaire example with three prompts per construct, response scales, language, scoring, source, and adaptation metadata. These app-generated items are examples, not a validated measure. Step 3 adds or imports custom variables and captures item text/source type, response scale, language, scoring, citation/URL, adaptation notes, and available validity/reliability evidence. Existing CSVs and saved plans remain usable. Step 4 builds a conceptual diagram; Step 5 reviews variables and downloads the matrices and draft survey.
3. **Community Data Repository Sync (Module 3):** Review permissions, identifiers, and disclosure risks; upload datasets to private or public storage with explicit confirmation; and review datasets available to your account.
4. **Descriptive & Scale Analytics (Module 4):** Select a dataset, map columns to Module 2 variables, inspect distributions and descriptive statistics, review composite scores, reliability, correlations, and download a report. Numeric mappings support composite scores and Cronbach's alpha for multi-item mappings; categorical mappings show response counts.
5. **Live Central Database Viewer (Module 5):** Select a repository table available to your account, browse authorized records, and download the displayed table as CSV.

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
No database or secrets setup is needed; deployments read the catalog file from
the same repository revision as `openscience.py`.

---

## 🤖 Community Theory and Variable Suggestions
Module 2 can submit a researcher's theory and variable map, literature rationale,
and conceptual relationships as a JSON file in `suggestions/`, on a new branch
with a pull request to `main`. Maintainers review and merge accepted suggestions;
submissions do not update the app's built-in catalog automatically. Contributors
must confirm that their submission contains no confidential or identifying
information. Pull requests are public, so do not include participant information,
private study details, unpublished results, or other sensitive content.

Configure `GITHUB_PAT` as a fine-grained token limited to this repository, with
Contents: Read and write and Pull requests: Read and write permissions. The token
is stored only in the Streamlit app's secrets and is not shown to researchers.
GitHub organization policies may require an administrator to approve the token.

---

## 📊 Core Cloud Architecture (Supabase Schema)

Data persistence is managed via an active cloud **Supabase** instance. The database utilizes a strictly connected relational cascade pattern (`ON DELETE CASCADE`) to bind survey parameters to core studies in the `public` schema layer:

```sql
-- 1. Parent Studies Ingestion Table
create table public.studies (
    id uuid primary key default gen_random_uuid(),
    study_title text not null,
    principal_investigator text,
    institution text,
    funding_source text,
    study_description text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 2. Child Variables Dictionary Table
create table public.variables (
    id uuid primary key default gen_random_uuid(),
    study_id uuid references public.studies(id) on delete cascade,
    variable_name text not null,
    variable_label text,
    data_type text,
    measurement_unit text,
    description text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);
```

### Researcher sign-in and dataset ownership

Visitors can navigate and read the module previews without signing in. Entering
study information, submitting proposals, uploading datasets, or accessing
account data requires a Supabase passwordless email link. Authenticated requests
are scoped by Supabase Row Level Security (RLS), and the app uses the Supabase
publishable/anon key rather than a service-role key.

Before enabling dataset uploads:

1. In Supabase Auth, enable email sign-in and set the Site URL and allowed
   redirect URL to the exact HTTPS URL where this Streamlit app is deployed.
2. In the Supabase email sign-in template, use a link that returns the token
   hash to Streamlit, for example:

   ```html
   <a href="{{ .RedirectTo }}/?token_hash={{ .TokenHash }}&type=email">Sign in</a>
   ```

   Confirm the redirect URL is allowlisted in Supabase Auth.
3. Run [`supabase/setup_auth_storage.sql`](supabase/setup_auth_storage.sql)
   in the Supabase SQL Editor. Review existing policies first; remove any older
   broad policies that grant anonymous or cross-user access to `studies`,
   `variables`, `study_datasets`, `study_discovery`, or `storage.objects`. PostgreSQL RLS policies
   are permissive by default when combined, so an old permissive policy can
   widen access. If Supabase was configured before Module 2 plan persistence
   was added, run the updated SQL script again to create the
   `study_module2_plans` table and its owner-scoped policies. The script also
   creates `study_discovery`: only summaries explicitly published by their
   owners are visible to signed-in researchers. The summary includes the study
   title, selected design/context metadata, and variable/measurement metadata;
   item text and participant data are excluded. Owners can remove a summary by
   turning off discovery sharing and saving their Module 2 plan.
4. Add the app secrets:

   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-publishable-or-anon-key"
   APP_URL = "https://your-deployed-streamlit-app.example"
   ```

The SQL creates a private `study-datasets` bucket and a separate public
`public-study-datasets` bucket. Private objects are restricted to their owner
through RLS. Public objects are downloadable by anyone with the file URL.
Module 3 requires extra confirmation before public release and displays the
public URL. Public release should only be used when the owner, consent,
agreements, and privacy review permit it; it may not be possible to retract
copies or links after release.

Module 4 lists datasets the signed-in user owns plus datasets marked public,
then downloads through Supabase Storage policies. Module 1 study records include
the authenticated owner's user ID. Existing rows without an owner remain
unavailable to signed-in users until an administrator reviews and assigns them.
Module 2 plans can be loaded and saved for a selected saved Module 1 study;
the plan JSON and conceptual diagram are stored in `study_module2_plans` and
are protected by owner-scoped RLS. Unsaved drafts remain downloadable but are
not stored in Supabase.
The app's permission/privacy prompts are attestations, not access controls,
IRB approval, or a determination that data are safe to share.

---

## ⚙️ Secrets Deployment Configuration

To host this application or configure an independent Streamlit Community Cloud mirror instance, populate your **App Secrets (`.toml`)** file inside your workspace management panel using this format:

```toml
# Cloud Data Warehouse Connection Tokens
# Use the Supabase publishable/anon key; do not use a service-role key.
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." # Extended anon/public client API key

APP_URL = "https://your-deployed-streamlit-app.example"

# Fine-grained GitHub token, limited to this repository:
# Contents: Read and write; Pull requests: Read and write
GITHUB_PAT = "your-fine-grained-token"
```

---

## 🚀 Local Installation & Setup

To run this application locally on your workstation for development or extension testing:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com
   cd openedmetadata
   ```

2. **Configure Environment Secrets:**
   Create a local directory configuration folder `.streamlit/` and place a `secrets.toml` file inside it containing your active keys:
   ```bash
   mkdir .streamlit
   touch .streamlit/secrets.toml
   ```

3. **Install Dependencies:**
   Ensure your Python environment is completely up to date and load the required library stack:
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Engine:**
   Run the boot sequence via your local Streamlit compiler:
   ```bash
   streamlit run openscience.py
   ```

---

## 📜 Dependencies Checklist (`requirements.txt`)
The minimal library environment grid required for this portal consists of:
```text
streamlit>=1.30.0
streamlit-flow-component>=1.6.1
pandas>=2.0.0
numpy>=1.24.0
supabase>=2.3.0
PyGithub>=2.1.0
matplotlib>=3.7.0
reportlab>=4.0.0
scipy>=1.10.0
statsmodels>=0.14.0
```

---

## 📄 License & Terms
Distributed under the **MIT License**. Other research institutions and education task forces are explicitly granted legal permission to copy, alter, scale, and redistribute this platform, provided proper attribution credit is maintained.

The instrument library in `library/` is licensed separately: records are CC BY-SA 4.0, and each instrument's item text carries its own license. See [`library/LICENSE.md`](library/LICENSE.md).
