# Changelog: HuMeta profile

## Unreleased

* **STEMEd+ disciplines, list version 5:** Human Dimensions no longer matches
  non-environmental uses such as "Human Dimensions of Organizations".
* **STEMEd+ disciplines, list version 4:** new **Human Dimensions** discipline
  (scope "field"; ANZSRC 4104 and 4406): human dimensions of natural resources,
  forestry, wildlife, fisheries, conservation, and climate change,
  social-ecological systems, environmental social science. Agriculture now
  covers agronomy, horticulture, crop, soil, weed, range, plant, and animal
  sciences, entomology, forestry, fisheries, food science, aquaculture, and
  Cooperative Extension (soil science stays Earth Science too; entomology and
  plant and animal sciences stay Bioscience too). "[Field] Science Teaching
  Professor" is no longer Science Education.
* **STEMEd+ disciplines, list version 3:** Engineering now includes computing
  (computer science, computing, computational thinking, cybersecurity) on every
  STEMEd+ site, not only STEMEd+ Funding. Mathematics also matches "math".
* **Shared STEMEd+ discipline list** (`stemedplus_disciplines.json`, with a
  JSON Schema). The ten disciplines used by STEMEd+ Jobs, Funding, Digest, and
  Graduate Programs now live here, each with an id, label, definition, the
  words that match it, and the HuMeta (ANZSRC) discipline terms it corresponds
  to. The sites build from it, so they define disciplines the same way.
* **Two new STEMEd+ disciplines** (list version 2): History & Philosophy of
  Science (HPS, history of medicine, science and technology studies, nature of
  science; ANZSRC 5002 and 4410) and Science & Health Communication (science,
  health, risk, climate, and environmental communication, public engagement,
  science and health journalism; ANZSRC 4701 and 4206). Unlike the others, both
  include the field itself, not only education in it.
* **New discipline term `discipline_general`** ("Not specific to a discipline")
  for instruments, theories, and studies that apply across subject areas. It
  has no ANZSRC or FOS code, so it is not exported as an ANZSRC or FOS subject.
* **The instrument library uses HuMeta vocabularies.** Instruments and evidence
  samples now record education levels (`education_level`), settings
  (`learning_environment`), who the instrument gathers data about
  (`participant_role`), disciplines (`discipline`, current ANZSRC terms only),
  and institution types (`institution_type`) with HuMeta terms; library-only
  terms were converted. Instrument types map to `data_collection_method`, and
  the library's reliability and validity rubric maps to `measurement_evidence`.
* **Instrument records export to DataCite 4.7** (typed `Text`, "Research
  instrument"), with the same subject schemes as study records, so a dataset's
  `IsCollectedBy` link points at an instrument described in the same terms.

* **ERIC descriptors for three terms that had none.** `study_design: ethnographic` →
  Ethnography; `data_collection_method: ethnography` → Ethnography, Participant Observation;
  `participant_role: educators` → Teachers, College Faculty, Teaching Assistants. Each was
  checked on its ERIC Thesaurus page.
* **All ERIC descriptors verified.** The 16 descriptors left unverified in
  1.0.0-draft.1 (Content Validity, Correlation, Critical Thinking, STEM
  Education, Stereotypes, Student Attitudes, Student Behavior, Student Centered
  Learning, Student Interests, Student Motivation, Student Records, Study
  Habits, Study Skills, Summer Programs, Surveys, Synchronous Communication)
  were checked against their ERIC Thesaurus term pages and are all current
  descriptors. They are now included in ERIC and DataCite exports.
* **Disciplines follow ANZSRC 2020 Fields of Research.** `study.discipline`
  now offers the 23 divisions and 213 groups of the ANZSRC 2020 FoR (from the
  official code set published by Stats NZ's research information system),
  each mapped to an OECD FOS code. Exported as DataCite subjects with the
  ANZSRC concept URI and code. The earlier 28 discipline terms are deprecated
  with `replaced_by` links, and `migrate` moves records to the new terms. FOS
  labels now cover all 48 OECD categories as DataCite labels them.
* **Measurement evidence is optional; rule R3 retired.**
  `study.evidence.measurement_evidence` is now optional (O) and is no longer
  asked in the portal's study profile; an instrument's reliability and
  validity evidence is recorded with the instrument in the instrument library.
  Rule R3 (instruments must list measurement evidence) is retired; its ID is
  not reused.
* **New field modules: Social Science and Arts and Humanities.** Starting
  points, to be developed with researchers in those fields.
  * `social_science`: `kind_of_data` (DDI KindOfData 1.0.0), `universe`,
    `geographic_unit`, `response_rate`, `weighting` (DDI-Codebook `universe`,
    `geogUnit`, `respRate`, `weight`), and `ddi_record`, a link to the study's
    full DDI documentation, exported as a DataCite related identifier
    (IsDocumentedBy). The module points to DDI rather than duplicating it.
  * `humanities`: `research_activities` (TaDiRAH 2.0.3, exported as DataCite
    subjects with TaDiRAH concept URIs), `objects_of_study`,
    `source_languages`, `editorial_standards`.
  * New vocabularies `kind_of_data` and `tadirah_activity`.
* **DDI-Codebook 2.5 export** (`oem/ddi.py`): the study profile, and the
  Module 2 variable plan when present, as DDI-Codebook XML. Unit of analysis,
  sampling, collection mode, time method, and kind of data carry their DDI
  controlled-vocabulary codes as `concept`; variables carry codes, missing
  codes, question text, and the construct they measure (`concept`, vocabulary
  "HuMeta Constructs"). Validated against the official DDI-Codebook 2.5.1
  schema, vendored for tests in `tests/schemas/ddi-codebook-2.5.1/` (LGPL-3.0). The example
    records for archival letters and online discourse use the new modules.
* **Renamed** from the STEMEd+ Metadata Application Profile to **HuMeta: The Social Science, Humanities, and Education Study Metadata Profile**, to serve the social sciences and humanities as well as education.
  Folder `standard/stemed-ap/` is now `standard/humeta/`; the record's `profile`
  value is `humeta`; DataCite subject schemes are named "HuMeta …".
* **Core and modules.** The record's `stemed` section is now `study` (the
  core). Education-specific elements moved to an optional **Education module**
  under the record key `education`: `education_levels`,
  `undergraduate_levels`, `institution_types` (from `context`), and
  `modality`, `learning_environments`, `pedagogy` (from `setting`). Education
  level is mandatory only when the module is used. Rule R11 (tribal college
  prompt) now reads the module's institution types.
* **Broader core for the social sciences and humanities.**
  * New `study.fields` (Research field, mandatory): education, social sciences,
    humanities, arts, other, with OECD Fields of Science codes, exported as
    DataCite FOS subjects.
  * `study.discipline` adds social-science and humanities disciplines, each
    with its FOS code.
  * New `study.population.human_participants` (direct / indirect / none).
    Participant roles are required only when people are involved; new roles
    for creators, online authors, and staff.
  * Unit of analysis and sampling procedure now follow the DDI AnalysisUnit
    and SamplingProcedure vocabularies (units now include texts, images,
    sound, video, and objects). Data collection methods, time-related designs,
    and source types map to DDI ModeOfCollection, TimeMethod,
    GeneralDataFormat, and DataSourceType. DDI-Codebook alignments added.
  * New methods: ethnography, archival research, corpus collection, web and
    platform data, visual and arts-based methods, diaries, recording,
    experiment, practice-based making. New designs: ethnographic, historical,
    interpretive or critical, practice-based.
  * New `study.evidence.analysis_methods`, including content and discourse
    analysis, close reading, visual analysis, and computational analysis.
  * New `study.sources` section (types, description, holdings, time period,
    rights), mandatory in type when no people take part.
  * New `study.ethics.online_data` practices and warning rules R13–R16 for
    public online data, following the AoIR ethical guidelines; R17 warns
    about sharing copies of copyrighted sources. R1 (constructs) now applies
    to instruments and to datasets with direct participants.
  * Two new examples: a study of public online posts and an archival
    humanities collection.
* **Theoretical framework.** New `study.design.frameworks` (recommended): the
  theories, lenses, or framework approaches (including the researcher's own
  framework, or an exploratory approach) that guide the study, from
  `library/frameworks.json`; plus `study.design.framework_description`.
  Exported as DataCite subjects (subjectScheme "HuMeta Frameworks") and in the
  Methods description.

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
* Reference implementation in the HuMeta Portal: Module 1 collects the profile, Module 3 adds constructs, checks
  rules, and exports (`oem/profile.py`).

### Before 1.0.0

* Public comment period, including review of the CARE elements by Indigenous
  data governance experts.
* ~~Confirm the remaining unverified ERIC descriptors.~~ Done.
* Replace provisional GitHub URIs for terms with persistent identifiers.
* Register a DOI for the 1.0.0 release.
