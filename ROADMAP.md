# Roadmap

HuMeta aims to give researchers in education, the social sciences, and the humanities shared infrastructure
for designing studies, choosing and administering instruments, describing
their data with common names and metadata, and sharing data responsibly.

## Foundation (done)

- Instrument library with constructs, versions, evidence, item crosswalks, and
  licensed item text (`library/`)
- Shared response scales, standard variables (including the 2024 federal
  race/ethnicity standard), and variable-naming rules (`oem/naming.py`)
- Codebook builder with CSV/JSON export (`oem/codebook.py`)
- App split into testable modules; CI with unit tests and page smoke tests
- Metadata profile 1.0.0-draft.1 with DataCite 4.7 and ERIC crosswalks; Module 1 is now the profile form
  and Module 3 checks and exports
- Renamed the profile to the HuMeta profile (`standard/humeta/`) and split it into a core plus an
  optional Education module; every field shows its alignments to DataCite, Dublin Core, schema.org and others

## Next

0. **HuMeta profile 1.0.** Public comment (including CARE review by Indigenous data governance experts),
   confirm remaining ERIC descriptors, persistent term URIs, DOI, and society endorsements
   (see `standard/humeta/endorsement/`).
0b. **Field modules and a broader core.** Working groups for the Social Science module (DDI-Codebook export
   for ICPSR, Dataverse and the UK Data Service; ELSST topics) and the Humanities module. Broaden core
   vocabularies (disciplines, data collection methods such as archival research, ethnography, content and
   discourse analysis), add a section for non-human sources (texts, artworks, media, platform data), and
   revisit rules that assume measured constructs or human participants.

1. **Connect Module 2 to the library.** Suggest instruments by construct, let
   researchers add library items as variables with generated names, export the
   study codebook, and retire `catalogs/measure_catalog.json` and the item text
   in `schema_config.json`.
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
5. **Automatic column matching** in Module 5 using the shared variable names.

## Good first issues

- Add the MSLQ items (public domain) and COPUS codes (CC BY-NC-SA 3.0) to
  `library/items/` from their source documents
- Resolve `needs_check` items in a library record by checking the cited source
- Propose a standard `gender` variable (needs community discussion; there is
  no settled federal standard to follow)
- Add response scales used by instruments in your field to `library/scales.json`
- Add type hints and docstrings to helpers in `oem/app/common.py`
- Improve accessibility of form labels and help text in a page
