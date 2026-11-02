# Changelog: STEMEd+ Metadata Application Profile

## Unreleased

* Every element now lists its alignments to DataCite, Dublin Core, schema.org,
  ERIC and other standards, with match type (exact, close, related);
  `crosswalks/alignments.csv` lists them all.
* Locale now uses the four NCES locale types (City, Suburb, Town, Rural) and is
  an exact match to NCES. `suburban` is renamed `suburb`. `online` and
  `multiple_locales` are removed: use Modality for online studies, and choose
  several locales for multi-site studies.

## 1.0.0-draft.1 (2026-11-01)

First public draft for community comment.

* Elements for constructs measured, discipline, population, institutional
  context, instructional setting, evidence (study design, measurement evidence,
  data collection methods), ethics and access, and CARE / Indigenous data
  governance, alongside DataCite-aligned citation metadata.
* 20 controlled vocabularies plus the 31-term construct vocabulary.
* Rules R1–R12 linking consent, identifiability, review status, and Indigenous
  data governance to declared access levels.
* Crosswalks to DataCite Metadata Schema 4.7 (validated against the official
  XML Schema) and the ERIC Thesaurus (with per-descriptor verification status).
* Reference implementation in OpenEdMetadata: Module 1 collects the profile, Module 3 adds constructs, checks
  rules, and exports (`oem/profile.py`).

### Before 1.0.0

* Public comment period, including review of the CARE elements by Indigenous
  data governance experts.
* Confirm the remaining unverified ERIC descriptors.
* Replace provisional GitHub URIs for terms with persistent identifiers.
* Register a DOI for the 1.0.0 release.
