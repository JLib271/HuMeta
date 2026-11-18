# Published records

Everything in this folder is **public**. The app reads it directly from the
deployed copy of this repository, so a merged pull request appears in the app
after Streamlit Community Cloud redeploys (it does this automatically on each
push to the deployed branch).

Researchers never write here directly: the app opens a pull request, and the
record is published only when a maintainer merges it. Research data are not
kept here: researchers deposit them in the STEMEd+ Commons Library
(Module 4).

| Folder | Contents | Created by |
| --- | --- | --- |
| `study_summaries/` | One `<study-id>.json` per published study summary (title, design/context metadata, variable and measurement metadata — never item text or participant data). | Module 2 → "Submit summary for public listing" |

## Reviewing a submission

Before merging:

1. Open the JSON in the pull request and check
   for names, emails, IDs, free-text responses, exact dates, small groups, or
   other details that could identify a person.
2. Check the title and description are accurate.
3. Remember that merged files stay in git history even if removed later, so
   anything published should be treated as permanent.

To remove a record, delete its files in a pull request (Module 2 can open a
removal request for a study summary). Removal stops it from being listed, but
earlier versions remain in the repository history.
