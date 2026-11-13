# Roadmap

HuMeta aims to give researchers in education, the social sciences, and the humanities shared infrastructure
for designing studies, choosing and administering instruments, describing
their data with common names and metadata, and sharing data responsibly.

## Foundation (done)

- Instrument library with constructs, versions, evidence, item crosswalks, and
  licensed item text, now in its own repository,
  [humeta-library](https://github.com/JLib271/humeta-library), which the portal reads from its website
- Shared response scales, standard variables (including the 2024 federal
  race/ethnicity standard), and variable-naming rules (`oem/naming.py`)
- Codebook builder with CSV/JSON export (`oem/codebook.py`)
- App split into testable modules; CI with unit tests and page smoke tests
- Metadata profile 1.0.0-draft.1 with DataCite 4.7 and ERIC crosswalks; Module 1 is now the profile form
  and Module 3 checks and exports
- Renamed the profile to the HuMeta profile (`standard/humeta/`) and split it into a core plus an
  optional Education module; every field shows its alignments to DataCite, Dublin Core, schema.org and others
- Module 2's framework library can be browsed by field, kind, and discipline and searched; 27 widely used
  theories and lenses added across sociology, political science, communication, economics, education, and the
  humanities and arts; every theory and lens is marked Draft until reviewed by experts
- Module 1 starts with the study's fields; new Social Science (DDI-based, linking to the study's DDI record) and
  Arts and Humanities (TaDiRAH) modules, as starting points for researchers in those fields

## Next

0. **HuMeta profile 1.0.** Public comment (including CARE review by Indigenous data governance experts),
   persistent term URIs, DOI, and society endorsements
   (see `standard/humeta/endorsement/`). The profile now has its own repository,
   [humeta-profile](https://github.com/JLib271/humeta-profile), with tagged releases; comment happens
   in its issues, and the portal moves to each release with `scripts/update_profile.py`.
0b. **Field modules and a broader core.** Working groups for the Social Science module (done: DDI-based
   fields, a link to the study's DDI record, and DDI-Codebook 2.5 export; next: ELSST topics, and a
   DDI-Lifecycle export so construct-to-question links travel as DDI concepts, ideally with the DDI
   Alliance) and the Arts and Humanities module. Broaden core
   vocabularies (disciplines, data collection methods such as archival research, ethnography, content and
   discourse analysis), add a section for non-human sources (texts, artworks, media, platform data), and
   revisit rules that assume measured constructs or human participants.

1. **Module 2 follow-ups.** Module 2 is now Framework and Measures, built on
   the library (frameworks, constructs, instruments, codebook). Next: let
   researchers pick individual library items, retire
   `catalogs/measure_catalog.json`, and move
   browsing (library, published studies, datasets) into one Explore page.
2. **Test builder.** Assemble a form from items whose license allows it
   (respecting `requires_item_ids`), export to Qualtrics import format, a
   printable document, and a codebook; otherwise show instrument suggestions
   with access routes.
3. **Study design templates.** Pre/post, randomized, quasi-experimental and
   correlational designs that set timepoints, plus data-sharing consent
   language to include in IRB materials.
4. **Responsible data sharing.** De-identification checks driven by variable
   sensitivity (direct identifiers, small cells, free text, dates), deposit
   packages (codebook + README) for repositories with access controls, and
   storing repository DOIs instead of hosting datasets in this repository.
5. **Module 5 next steps.** Done: automatic column matching, analysis by construct with pingouin, group and before/after comparisons, chi-square, linear and logistic regression, and an R script (psych and base R). Next: confirmatory factor analysis (lavaan or semopy) and measurement invariance across groups, as recommended by researchers.

## Good first issues

Library contributions (adding items, resolving `needs_check`, response scales) now live in
[humeta-library](https://github.com/JLib271/humeta-library).

- Propose a standard `gender` variable (needs community discussion; there is
  no settled federal standard to follow)
- Add type hints and docstrings to helpers in `oem/app/common.py`
- Improve accessibility of form labels and help text in a page
