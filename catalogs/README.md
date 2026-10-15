# Research Measure Catalog

Add reviewed measure records to [`measure_catalog.json`](measure_catalog.json).
Module 2 reads this file when it opens and displays entries matching an included
theory-derived or demographic/contextual variable, selected framework, and (when
available) the saved Module 1 research subject areas.

Keep the catalog empty until an entry has a verifiable source. Do not treat a
suggestion as validated just because it is listed. Check the instrument's
primary publication and fit for the intended population, language, context, and
research use before recommending it.

Each entry must include every field below. Use arrays for `discipline`,
`study_area`, `theory_framework`, `population_context`, and `response_format`
when an entry applies to more than one value. Use `["*"]` only when an entry is
intentionally not limited by that category. Entries with an empty array are
also treated as broadly applicable for filtering.

```json
{
  "measure_id": "unique-stable-id",
  "discipline": ["Education"],
  "study_area": ["Science education"],
  "variable": "Knowledge",
  "theory_framework": ["Theoretical Domains Framework (TDF)"],
  "measure_name": "Full instrument or measure name",
  "population_context": ["Population and context tested"],
  "response_format": ["Multiple choice"],
  "scoring": "Describe the scoring method and score interpretation.",
  "validity_evidence": "Summarize evidence and population; cite its source.",
  "reliability_evidence": "Summarize evidence and population; cite its source.",
  "citation": "Full bibliographic citation.",
  "doi_url": "https://doi.org/...",
  "source_url": "https://...",
  "license": "License or terms of use; explain if unclear.",
  "notes": "Limitations, permissions, adaptation, and review notes."
}
```

Use the exact Module 1 subject-area labels where possible. `variable` should
match a Module 2 factor or selected demographic/contextual variable. Framework
names should match the Module 2 catalog. Never add copyrighted instrument
items, confidential content, participant data, or claims unsupported by the
citation. The application shows measure descriptions and source details; it
does not reproduce test items or determine whether an instrument is valid for a
particular study.
