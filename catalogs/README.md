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

## Module 2 reference catalog

[`module2_catalog.json`](module2_catalog.json) contains the selectable theory
frameworks and variables, framework citations and suggested relationship paths,
demographic/contextual variable options, data-type choices, collection methods,
and illustrative TPB examples. Module 2 reads this file at runtime; it does not
require a database migration.

To edit these options, update the relevant catalog values while preserving the
JSON structure, then run the app and review Module 2. Theory records have a
unique `name`, a `variables` list, and a `citation`. Each relationship path is
an array of `[source variable, target variable, label]`. Quantitative and
qualitative collection methods are stored in separate lists. TPB example
templates use placeholders such as `{behavior_phrase}`, `{action}`,
`{context_phrase}`, `{timeframe_phrase}`, `{behavior_period}`, `{construct}`,
and `{topic}`.

The examples are app-generated illustrations, not validated measures. Review
their wording, fit, and permissions before using them in research.
