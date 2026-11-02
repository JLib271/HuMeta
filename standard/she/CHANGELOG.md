# Changelog: SHE Study Metadata Profile

## Unreleased

* **Renamed** from the STEMEd+ Metadata Application Profile to the SHE Study
  Metadata Profile (Social Science, Humanities, and Education Study Metadata
  Profile), to serve the social sciences and humanities as well as education.
  Folder `standard/stemed-ap/` is now `standard/she/`; the record's `profile`
  value is `she`; DataCite subject schemes are named "SHE …".
* **Core and modules.** The record's `stemed` section is now `study` (the
  core). Education-specific elements moved to an optional **Education module**
  under the record key `education`: `education_levels`,
  `undergraduate_levels`, `institution_types` (from `context`), and
  `modality`, `learning_environments`, `pedagogy` (from `setting`). Education
  level is mandatory only when the module is used. Rule R11 (tribal college
  prompt) now reads the module's institution types.

* Every element now lists its alignments to DataCite, Dublin Core, schema.org,
  ERIC and other standards, with match type (exact, close, related);
  `crosswalks/alignments.csv` lists them all.
* Locale now uses the four NCES locale types (City, Suburb, Town, Rural) and is
  an exact match to NCES. `suburban` is renamed `suburb`. `online` and
  `multiple_locales` are removed: use Modality for online studies, and choose
  several locales for multi-site studies.
* Education level now uses the nine UNESCO ISCED 2011 levels (0–8), plus
  adult/workforce education and informal learning. `elementary`,
  `middle_school`, `high_school`, `undergraduate` and `graduate` are replaced
  by `primary`, `lower_secondary`, `upper_secondary`, `bachelors`, `masters`
  and `doctoral`. `postsecondary_non_tertiary` and `short_cycle_tertiary` are
  new. DataCite exports include the ISCED level as a subject.
* The Dublin Core and schema.org alignments for education level, and the Dublin
  Core alignment for instructional approach, are marked as seeking expert input.

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
