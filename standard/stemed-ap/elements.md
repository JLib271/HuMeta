# STEMEd+ Metadata Application Profile: elements and vocabularies

Version 1.0.0-draft.1 (draft). Generated from `profile.json` and `vocabularies.json` by `scripts/build_profile_artifacts.py`; do not edit by hand.

Obligations: **M** = Mandatory: every record must have it.; **MA** = Mandatory if applicable: required when the stated condition holds.; **R** = Recommended.; **O** = Optional.

Alignments: each element lists the standards it corresponds to. No mark = exact match; **≈** = close match; **~** = related. `STEMEd+` = defined by this profile, with no equivalent in a general-purpose standard. Full list in [`crosswalks/alignments.csv`](crosswalks/alignments.csv).

Standards: [STEMEd+](https://github.com/JLib271/OpenEdMetadata/blob/main/standard/stemed-ap/README.md) = STEMEd+ Metadata Application Profile (extension element or vocabulary); [DataCite](https://schema.datacite.org/) = DataCite Metadata Schema 4.7; [DC](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/) = Dublin Core (DCMI Metadata Terms); [schema.org](https://schema.org/Dataset) = schema.org Dataset; [ERIC](https://eric.ed.gov/?ti=all) = ERIC Thesaurus; [ORCID](https://orcid.org/) = ORCID iD; [SPDX](https://spdx.org/licenses/) = SPDX License List; [BCP 47](https://www.rfc-editor.org/info/bcp47) = IETF BCP 47 language tags; [ISO 3166](https://www.iso.org/iso-3166-country-codes.html) = ISO 3166-1 alpha-2 country codes; [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) = ISO 8601 dates; [NCES](https://nces.ed.gov/programs/edge/Geographic/LocaleBoundaries) = NCES locale classification (locale types City, Suburb, Town, Rural); [AERA/APA/NCME](https://www.testingstandards.net/) = Standards for Educational and Psychological Testing (2014); [Common Rule](https://www.hhs.gov/ohrp/regulations-and-policy/regulations/45-cfr-46/) = US Common Rule for human-subjects research (45 CFR 46); [FERPA](https://studentprivacy.ed.gov/) = Family Educational Rights and Privacy Act (34 CFR Part 99); [CARE](https://www.gida-global.org/care) = CARE Principles for Indigenous Data Governance; [Local Contexts](https://localcontexts.org/) = Local Contexts Traditional Knowledge and Biocultural Labels and Notices

## Elements

| Element | Obligation | Cardinality | Definition | Aligned with | DataCite 4.7 mapping |
|---|---|---|---|---|---|
| <a id="resource.title"></a>`resource.title` | M | 1 | Name of the resource. | `DataCite: titles.title`, `DC: title`, `schema.org: name` | titles.title |
| <a id="resource.creators"></a>`resource.creators` | M | 1..n | People or organizations primarily responsible for the resource, with ORCID iDs where available. | `DataCite: creators`, `DC: creator`, `schema.org: creator`, `ORCID: ORCID iD (nameIdentifier)` | creators (nameIdentifier with nameIdentifierScheme ORCID; affiliation) |
| <a id="resource.publisher"></a>`resource.publisher` | M | 1 | Entity that holds, archives, or makes the resource available (usually the repository or institution). | `DataCite: publisher`, `DC: publisher`, `schema.org: publisher` | publisher |
| <a id="resource.publication_year"></a>`resource.publication_year` | M | 1 | Year the resource was or will be made publicly available. | `DataCite: publicationYear`, `≈DC: issued`, `≈schema.org: datePublished` | publicationYear |
| <a id="resource.resource_type"></a>`resource.resource_type` | M | 1 | General type of the resource, using DataCite resourceTypeGeneral values. | `DataCite: resourceTypeGeneral`, `≈DC: type`, `≈schema.org: @type` | types.resourceTypeGeneral; types.resourceType = 'STEMEd+ <type>' |
| <a id="resource.identifier"></a>`resource.identifier` | O | 0..1 | Persistent identifier (DOI preferred) once one has been assigned. | `DataCite: identifier`, `DC: identifier`, `schema.org: identifier` | identifiers (DOI) or alternateIdentifiers |
| <a id="resource.description"></a>`resource.description` | R | 0..1 | Abstract or summary of the resource. | `DataCite: description (Abstract)`, `DC: abstract`, `schema.org: description` | descriptions (descriptionType Abstract) |
| <a id="resource.keywords"></a>`resource.keywords` | O | 0..n | Free-text keywords. | `DataCite: subject (no scheme)`, `≈DC: subject`, `schema.org: keywords` | subjects (no scheme) |
| <a id="resource.language"></a>`resource.language` | R | 0..1 | Primary language of the resource (BCP 47 code, e.g. en). | `DataCite: language`, `DC: language`, `schema.org: inLanguage`, `BCP 47: language tag` | language |
| <a id="resource.license"></a>`resource.license` | R | 0..1 | License for the resource, as an SPDX identifier where possible (e.g. CC-BY-4.0). | `DataCite: rightsList`, `DC: license`, `schema.org: license`, `SPDX: license identifier` | rightsList (rightsIdentifier, rightsIdentifierScheme SPDX) |
| <a id="resource.funding"></a>`resource.funding` | O | 0..n | Funders and award numbers. | `DataCite: fundingReferences`, `≈schema.org: funder` | fundingReferences |
| <a id="resource.collection_dates"></a>`resource.collection_dates` | R | 0..1 | Start and end of data collection (ISO 8601 dates). | `DataCite: date (Collected)`, `ISO 8601: date`, `~DC: temporal`, `~schema.org: temporalCoverage` | dates (dateType Collected, as start/end) |
| <a id="resource.geography"></a>`resource.geography` | R | 0..1 | Countries (ISO 3166-1 alpha-2) and, for the US, states (USPS codes) where data were collected. | `DataCite: geoLocationPlace`, `ISO 3166: country code`, `≈DC: spatial`, `≈schema.org: spatialCoverage` | geoLocations (geoLocationPlace) |
| <a id="resource.related"></a>`resource.related` | O | 0..n | Related publications, datasets, preregistrations, or instruments, with a DataCite relationType. | `DataCite: relatedIdentifiers`, `≈DC: relation`, `~schema.org: citation` | relatedIdentifiers |
| <a id="stemed.design.topic"></a>`stemed.design.topic` | R | 0..1 | The main subject or topic of the study, in the researcher's words (e.g., 'introductory geology lab learning'). | `STEMEd+`, `≈DataCite: subject`, `≈DC: subject`, `≈schema.org: about` | subjects (no scheme) |
| <a id="stemed.design.research_questions"></a>`stemed.design.research_questions` | R | 0..1 | Primary research questions, objectives, or hypotheses. | `STEMEd+`, `≈DataCite: description (Methods)`, `~DC: description` | descriptions (descriptionType Methods) |
| <a id="stemed.design.unit_of_analysis"></a>`stemed.design.unit_of_analysis` | O | 0..n | The unit(s) the analysis is about. Vocabulary: [unit_of_analysis](#unit_of_analysis). | `STEMEd+`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'STEMEd+ Units of Analysis') |
| <a id="stemed.design.sampling_procedure"></a>`stemed.design.sampling_procedure` | O | 0..n | How participants or units were selected. Vocabulary: [sampling_procedure](#sampling_procedure). | `STEMEd+`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'STEMEd+ Sampling Procedures'); descriptions (Methods) |
| <a id="stemed.constructs"></a>`stemed.constructs` | MA | 0..n | Constructs measured, from the STEMEd+ construct vocabulary (library/constructs.json), optionally with the instrument, version and subscale used. *Mandatory when resource_type is Dataset or Instrument.* | `STEMEd+`, `≈ERIC: descriptors`, `≈schema.org: variableMeasured`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'STEMEd+ Constructs', valueURI per construct); for datasets, relatedIdentifiers to the instrument's library record (URL, relationType IsCollectedBy) and its publication (DOI, relationType References); ERIC descriptors as additional subjects |
| <a id="stemed.discipline"></a>`stemed.discipline` | R | 0..n | STEM discipline(s) of the learning or research. Vocabulary: [discipline](#discipline). | `STEMEd+`, `≈ERIC: descriptors`, `≈DC: subject`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'STEMEd+ Disciplines') |
| <a id="stemed.population.participant_roles"></a>`stemed.population.participant_roles` | M | 1..n | Who the participants are. Vocabulary: [participant_role](#participant_role). | `STEMEd+`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'STEMEd+ Participant Roles') |
| <a id="stemed.population.education_levels"></a>`stemed.population.education_levels` | M | 1..n | Education level(s) of the participants. Vocabulary: [education_level](#education_level). | `STEMEd+`, `≈ERIC: education level descriptors`, `≈DC: educationLevel`, `≈schema.org: educationalLevel` | subjects (subjectScheme 'STEMEd+ Education Levels') |
| <a id="stemed.population.undergraduate_levels"></a>`stemed.population.undergraduate_levels` | O | 0..n | Course level(s) for undergraduate studies. Vocabulary: [undergraduate_level](#undergraduate_level). | `STEMEd+`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'STEMEd+ Undergraduate Levels') |
| <a id="stemed.population.description"></a>`stemed.population.description` | R | 0..1 | Narrative description of the participants and sampling, without identifying information. | `STEMEd+`, `≈DataCite: description (Methods)` | descriptions (descriptionType Methods) |
| <a id="stemed.population.sample_size"></a>`stemed.population.sample_size` | R | 0..1 | Number of participants (or units) in the data. | `STEMEd+`, `≈DataCite: sizes` | sizes ('N = <n> participants') |
| <a id="stemed.context.institution_types"></a>`stemed.context.institution_types` | R | 0..n | Type(s) of institution or organization. Vocabulary: [institution_type](#institution_type). | `STEMEd+`, `≈ERIC: descriptors` | subjects (subjectScheme 'STEMEd+ Institution Types') |
| <a id="stemed.context.locale"></a>`stemed.context.locale` | R | 0..n | Community type(s) where the study took place. Vocabulary: [locale](#locale). | `STEMEd+`, `NCES: locale type`, `≈ERIC: descriptors` | subjects (subjectScheme 'STEMEd+ Locales') |
| <a id="stemed.setting.modality"></a>`stemed.setting.modality` | R | 0..n | How instruction or participation was delivered. Vocabulary: [modality](#modality). | `STEMEd+`, `≈ERIC: descriptors` | subjects (subjectScheme 'STEMEd+ Modalities') |
| <a id="stemed.setting.learning_environments"></a>`stemed.setting.learning_environments` | R | 0..n | Instructional setting(s). Vocabulary: [learning_environment](#learning_environment). | `STEMEd+`, `≈ERIC: descriptors` | subjects (subjectScheme 'STEMEd+ Learning Environments') |
| <a id="stemed.setting.pedagogy"></a>`stemed.setting.pedagogy` | O | 0..n | Instructional approach(es) used or studied. Vocabulary: [pedagogy](#pedagogy). | `STEMEd+`, `≈ERIC: descriptors`, `≈DC: instructionalMethod` | subjects (subjectScheme 'STEMEd+ Instructional Approaches') |
| <a id="stemed.evidence.study_designs"></a>`stemed.evidence.study_designs` | MA | 0..n | Design(s) that produced the evidence. *Mandatory when resource_type is Dataset or StudyRegistration.* Vocabulary: [study_design](#study_design). | `STEMEd+`, `≈ERIC: descriptors`, `≈DataCite: description (Methods)` | subjects (subjectScheme 'STEMEd+ Study Designs'); descriptions (Methods) |
| <a id="stemed.evidence.measurement_evidence"></a>`stemed.evidence.measurement_evidence` | MA | 0..n | Kinds of reliability and validity evidence the resource provides. *Mandatory when resource_type is Instrument.* Vocabulary: [measurement_evidence](#measurement_evidence). | `STEMEd+`, `≈AERA/APA/NCME: sources of validity evidence`, `≈ERIC: descriptors` | subjects (subjectScheme 'STEMEd+ Measurement Evidence') |
| <a id="stemed.evidence.data_collection_methods"></a>`stemed.evidence.data_collection_methods` | R | 0..n | How data were collected. Vocabulary: [data_collection_method](#data_collection_method). | `STEMEd+`, `≈ERIC: descriptors`, `≈schema.org: measurementTechnique` | subjects (subjectScheme 'STEMEd+ Data Collection Methods') |
| <a id="stemed.ethics.human_subjects_review"></a>`stemed.ethics.human_subjects_review` | M | 1 | Ethics / IRB review status, as reported by the researcher. Vocabulary: [human_subjects_review](#human_subjects_review). | `STEMEd+`, `~Common Rule: IRB review / exemption` | descriptions (descriptionType Other, 'Ethics and access') |
| <a id="stemed.ethics.consent"></a>`stemed.ethics.consent` | R | 0..1 | How participants agreed to take part. Vocabulary: [consent](#consent). | `STEMEd+`, `~Common Rule: informed consent / waiver` | descriptions (Other, 'Ethics and access') |
| <a id="stemed.ethics.consent_for_sharing"></a>`stemed.ethics.consent_for_sharing` | M | 1 | What participants allow regarding sharing beyond the research team. Vocabulary: [consent_for_sharing](#consent_for_sharing). | `STEMEd+`, `~schema.org: conditionsOfAccess`, `~DataCite: rightsList` | descriptions (Other, 'Ethics and access'); rightsList |
| <a id="stemed.ethics.identifiability"></a>`stemed.ethics.identifiability` | M | 1 | Identifiability of the data. Vocabulary: [identifiability](#identifiability). | `STEMEd+`, `~FERPA: de-identified records` | descriptions (Other, 'Ethics and access') |
| <a id="stemed.ethics.sensitivity_flags"></a>`stemed.ethics.sensitivity_flags` | R | 0..n | Kinds of sensitive information in the underlying data. Vocabulary: [sensitivity_flag](#sensitivity_flag). | `STEMEd+`, `≈FERPA: education records` | descriptions (Other, 'Ethics and access') |
| <a id="stemed.ethics.access_level"></a>`stemed.ethics.access_level` | M | 1 | How the data can be accessed. Vocabulary: [access_level](#access_level). | `STEMEd+`, `≈DC: accessRights`, `≈schema.org: conditionsOfAccess`, `≈DataCite: rightsList` | rightsList (access statement) |
| <a id="stemed.ethics.governance_notes"></a>`stemed.ethics.governance_notes` | O | 0..1 | Approval references, data-use restrictions, retention or de-identification requirements (no confidential details). | `STEMEd+`, `~DC: accessRights`, `≈DataCite: description (Other)` | descriptions (Other, 'Ethics and access') |
| <a id="stemed.care.indigenous_data"></a>`stemed.care.indigenous_data` | M | 1 | Whether the resource contains or derives from data about Indigenous Peoples, nations, communities, lands, territories, or knowledges. Vocabulary: [indigenous_data](#indigenous_data). | `STEMEd+`, `≈CARE: scope: Indigenous data` | descriptions (Other, 'CARE statement') |
| <a id="stemed.care.governance"></a>`stemed.care.governance` | MA | 0..1 | How Indigenous authority to control the data is exercised (CARE: Authority to control). *Mandatory when indigenous_data is yes.* Vocabulary: [indigenous_governance](#indigenous_governance). | `STEMEd+`, `≈CARE: Authority to control` | descriptions (Other, 'CARE statement'); rightsList |
| <a id="stemed.care.statement"></a>`stemed.care.statement` | MA | 0..1 | How the work provides collective benefit, respects authority to control, and meets responsibility and ethics obligations to the communities involved. *Mandatory when indigenous_data is yes.* | `STEMEd+`, `≈CARE: Collective benefit; Responsibility; Ethics`, `≈DataCite: description (Other)` | descriptions (Other, 'CARE statement') |
| <a id="stemed.care.local_contexts_project"></a>`stemed.care.local_contexts_project` | O | 0..1 | URL of a Local Contexts Hub project holding Traditional Knowledge or Biocultural Labels or Notices for this resource. | `Local Contexts: Hub project`, `≈DataCite: relatedIdentifier` | relatedIdentifiers (relatedIdentifierType URL, relationType IsDescribedBy) |
| <a id="stemed.care.local_contexts_labels"></a>`stemed.care.local_contexts_labels` | O | 0..n | Names of Local Contexts Labels or Notices applied by the community (e.g. 'TK Attribution'). | `Local Contexts: TK/BC Labels and Notices` | descriptions (Other, 'CARE statement') |

## Rules

| Rule | Severity | Requirement |
|---|---|---|
| R1 | error | Datasets and instruments must list at least one construct measured. |
| R2 | error | Datasets and study registrations must list at least one study design. |
| R3 | error | Instruments must list at least one kind of measurement evidence. |
| R4 | error | Open access requires data that are de-identified, anonymous, aggregate-only, synthetic, or not participant data. |
| R5 | error | Open access requires consent for broad sharing (or no human-subjects data). |
| R6 | error | Data cannot be open or registered-access while human-subjects review is 'not yet assessed' or 'pending'. |
| R7 | error | Indigenous data require a governance arrangement and a CARE statement. |
| R8 | error | Indigenous data may be open only under a community data governance agreement or tribal review approval. |
| R9 | warning | Data from education records (FERPA): confirm the institution's FERPA review before any sharing. |
| R10 | warning | Indigenous data status is unknown; assess it before sharing. |
| R11 | warning | A specific community or a tribal college is involved; confirm whether the data are Indigenous data. |
| R12 | warning | Direct identifiers are flagged; they must be removed before the data are shared. |

## Vocabularies

### <a id="discipline"></a>STEM discipline (`discipline`)

Disciplinary content area of the learning or research studied.

| Code | Label | ERIC descriptors |
|---|---|---|
| `biology` | Biology and life sciences | Biology |
| `chemistry` | Chemistry | Chemistry |
| `physics` | Physics | Physics |
| `geoscience` | Geoscience / Earth science | Earth Science, Geology |
| `climate_science` | Climate and environmental science | Climate, Earth Science |
| `astronomy` | Astronomy and space science | Astronomy |
| `mathematics` | Mathematics and statistics | Mathematics Education |
| `computer_science` | Computer science and computing | Computer Science Education |
| `engineering` | Engineering | Engineering Education |
| `general_stem` | General or interdisciplinary STEM | Science Education, STEM Education (unverified) |
| `other_discipline` | Other discipline |  |

### <a id="education_level"></a>Education level (`education_level`)

Education level(s) of the learners or participants.

| Code | Label | ERIC descriptors |
|---|---|---|
| `early_childhood` | Early childhood / pre-K | Early Childhood Education |
| `elementary` | Elementary / primary | Elementary Education |
| `middle_school` | Middle grades / lower secondary | Middle Schools, Secondary Education |
| `high_school` | High school / upper secondary | High Schools, Secondary Education |
| `undergraduate` | Undergraduate | Higher Education, Postsecondary Education, Undergraduate Students |
| `graduate` | Graduate / professional | Higher Education, Graduate Students |
| `adult_education` | Adult, continuing, or workforce education | Adult Education, Adults |
| `informal_learning` | Informal or out-of-school learning (any age) | Informal Education |

### <a id="undergraduate_level"></a>Undergraduate course level (`undergraduate_level`)

For undergraduate studies, the course level(s) involved.

| Code | Label | ERIC descriptors |
|---|---|---|
| `introductory` | Introductory / first-year |  |
| `intermediate` | Intermediate / second-year |  |
| `advanced` | Advanced / third- or fourth-year |  |
| `capstone` | Upper-division / capstone |  |

### <a id="participant_role"></a>Participant population (`participant_role`)

Who the participants are.

| Code | Label | ERIC descriptors |
|---|---|---|
| `students` | Students / learners |  |
| `educators` | Teachers, instructors, or teaching assistants |  |
| `professionals` | Researchers or other professionals |  |
| `children_youth` | Children or youth |  |
| `adults` | Adults | Adults |
| `families` | Families or household groups |  |
| `visitors` | Museum, science-center, or event visitors | Museums |
| `community_members` | Community members / general public |  |
| `specific_community` | A specific community or cultural group |  |
| `other_participants` | Other participants |  |

### <a id="institution_type"></a>Institution or organization type (`institution_type`)

Type(s) of institution or organization where the study took place.

| Code | Label | ERIC descriptors |
|---|---|---|
| `k12_public` | Public K-12 school | Public Schools |
| `k12_private` | Private K-12 school | Private Schools |
| `two_year_college` | Two-year / community college | Two Year Colleges |
| `four_year_college` | Four-year college or primarily undergraduate institution | Higher Education |
| `research_university` | Research university | Research Universities |
| `minority_serving` | Minority-serving institution | Minority Serving Institutions |
| `hbcu` | Historically Black college or university | Black Colleges, Minority Serving Institutions |
| `tribal_college` | Tribal college or university | Tribally Controlled Education, Minority Serving Institutions |
| `museum_science_center` | Museum, science center, or library | Museums |
| `community_organization` | Community organization | Community Organizations |
| `online_provider` | Online learning provider | Distance Education |
| `other_institution` | Other |  |

### <a id="locale"></a>Locale (`locale`)

Community type where the study took place, using the four NCES locale types. Choose more than one for multi-site studies. For fully online studies, leave blank and use Modality.

| Code | Label | ERIC descriptors |
|---|---|---|
| `city` | City (NCES 11–13) | Urban Areas |
| `suburb` | Suburb (NCES 21–23) |  |
| `town` | Town (NCES 31–33) |  |
| `rural` | Rural (NCES 41–43) | Rural Areas |

### <a id="modality"></a>Instructional modality (`modality`)

How instruction or participation was delivered.

| Code | Label | ERIC descriptors |
|---|---|---|
| `in_person` | In person |  |
| `online_synchronous` | Online, synchronous | Online Courses, Synchronous Communication (unverified) |
| `online_asynchronous` | Online, asynchronous | Online Courses, Asynchronous Communication |
| `hybrid` | Hybrid / blended | Blended Learning |
| `not_instructional` | Not an instructional setting |  |

### <a id="learning_environment"></a>Learning environment (`learning_environment`)

The instructional setting in which learning or data collection took place.

| Code | Label | ERIC descriptors |
|---|---|---|
| `large_lecture` | Large lecture class | Large Group Instruction, Lecture Method |
| `small_class` | Small class, seminar, recitation, or discussion section | Small Group Instruction |
| `laboratory` | Laboratory | Laboratories, Science Laboratories |
| `field` | Field course, field trip, or field site | Field Trips |
| `online_course` | Online course environment | Online Courses |
| `museum_exhibit` | Museum, exhibit, or science center | Museums, Informal Education |
| `out_of_school_program` | Afterschool, summer, or out-of-school program | After School Programs, Summer Programs (unverified) |
| `community_or_public_space` | Community setting, public space, or event |  |
| `home_family` | Home or family setting |  |
| `workplace` | Workplace or professional setting |  |
| `k12_classroom` | K-12 classroom |  |
| `postsecondary_classroom` | College or university classroom |  |
| `other_environment` | Other |  |

### <a id="pedagogy"></a>Instructional approach (`pedagogy`)

Main instructional approach(es) used or studied (optional).

| Code | Label | ERIC descriptors |
|---|---|---|
| `lecture_based` | Lecture-based | Lecture Method |
| `active_learning` | Active learning | Active Learning |
| `inquiry_based` | Inquiry-based | Inquiry |
| `problem_project_based` | Problem- or project-based | Problem Based Learning |
| `flipped` | Flipped classroom | Flipped Classroom |
| `student_centered` | Student-centered | Student Centered Learning (unverified) |
| `research_experience` | Course-based or apprenticed research experience | Undergraduate Study |
| `other_pedagogy` | Other |  |

### <a id="study_design"></a>Study design (evidence type) (`study_design`)

The design that produced the evidence in the resource.

| Code | Label | ERIC descriptors |
|---|---|---|
| `cross_sectional` | Cross-sectional (single time point) |  |
| `descriptive` | Descriptive | Educational Research |
| `correlational` | Correlational | Correlation (unverified) |
| `quasi_experimental` | Quasi-experimental | Quasiexperimental Design |
| `randomized_experiment` | Randomized experiment | Randomized Controlled Trials |
| `longitudinal` | Longitudinal | Longitudinal Studies |
| `pre_post` | Pre/post measurement around an intervention |  |
| `time_series` | Time series |  |
| `qualitative` | Qualitative | Qualitative Research |
| `mixed_methods` | Mixed methods | Mixed Methods Research |
| `case_study` | Case study | Case Studies |
| `design_based` | Design-based research | Research Design |
| `program_evaluation` | Program evaluation | Program Evaluation |
| `instrument_development` | Instrument development or validation | Test Construction, Psychometrics |
| `secondary_analysis` | Secondary analysis of existing data | Data Analysis |
| `meta_analysis` | Meta-analysis or systematic review | Meta Analysis |
| `replication` | Replication | Replication (Evaluation) |

### <a id="unit_of_analysis"></a>Unit of analysis (`unit_of_analysis`)

The unit the analysis is about.

| Code | Label | ERIC descriptors |
|---|---|---|
| `individual` | Individual (person / participant) |  |
| `group` | Group, household, or community |  |
| `organization` | Organization or institution |  |
| `place` | Place, site, or geographic area |  |
| `event` | Event, activity, or interaction |  |
| `artifact` | Document, artifact, or media object |  |
| `multilevel` | Other or multi-level |  |

### <a id="sampling_procedure"></a>Sampling procedure (`sampling_procedure`)

How participants or units were selected.

| Code | Label | ERIC descriptors |
|---|---|---|
| `census` | Census of all eligible units |  |
| `convenience` | Convenience sample |  |
| `volunteer` | Volunteer / self-selected |  |
| `purposive` | Purposive / criterion-based |  |
| `stratified` | Stratified sample |  |
| `cluster` | Cluster or multistage sample |  |
| `random` | Random sample within sites |  |
| `systematic` | Systematic sample from a list |  |
| `time_location` | Time-location or venue-based sample |  |
| `snowball` | Snowball / peer referral |  |
| `mixed_sampling` | Multiple or mixed procedures |  |
| `other_sampling` | Other |  |

### <a id="measurement_evidence"></a>Measurement evidence (`measurement_evidence`)

Kinds of reliability or validity evidence the resource provides, following the sources of validity evidence in the Standards for Educational and Psychological Testing (AERA, APA, NCME, 2014).

| Code | Label | ERIC descriptors |
|---|---|---|
| `test_content` | Evidence based on test content | Content Validity (unverified), Test Validity |
| `response_processes` | Evidence based on response processes | Test Validity |
| `internal_structure` | Evidence based on internal structure | Construct Validity, Factor Analysis |
| `relations_to_other_variables` | Evidence based on relations to other variables | Predictive Validity, Test Validity |
| `consequences` | Evidence based on consequences of testing | Test Validity |
| `reliability` | Reliability / precision | Test Reliability |
| `fairness` | Fairness / differential item functioning | Test Bias |
| `irt_scaling` | Item response theory scaling | Item Response Theory |

### <a id="data_collection_method"></a>Data collection method (`data_collection_method`)

How data were collected.

| Code | Label | ERIC descriptors |
|---|---|---|
| `survey` | Survey or questionnaire | Questionnaires, Surveys (unverified) |
| `assessment` | Test or assessment | Tests |
| `observation` | Observation | Observation, Classroom Observation Techniques |
| `interview` | Interview | Interviews |
| `focus_group` | Focus group | Focus Groups |
| `artifacts` | Student work, documents, or artifacts | Content Analysis |
| `learning_analytics` | Learning analytics or log data | Learning Analytics |
| `institutional_records` | Institutional or administrative records | Student Records (unverified) |
| `other_method` | Other |  |

### <a id="human_subjects_review"></a>Human-subjects review (`human_subjects_review`)

Status of ethics / IRB review, as reported by the researcher.

| Code | Label | ERIC descriptors |
|---|---|---|
| `approved` | Approved |  |
| `exempt` | Exempt determination |  |
| `not_human_subjects` | Determined not to be human-subjects research |  |
| `pending` | Submitted / pending |  |
| `not_assessed` | Not yet assessed |  |
| `other_review` | Other |  |

### <a id="consent"></a>Participation consent (`consent`)

How participants agreed to take part.

| Code | Label | ERIC descriptors |
|---|---|---|
| `informed_consent` | Informed consent | Informed Consent |
| `permission_and_assent` | Parent/guardian permission and participant assent | Informed Consent |
| `waiver` | Waiver or alteration of consent |  |
| `not_applicable` | Not applicable |  |
| `not_assessed` | Not yet assessed |  |
| `other_consent` | Other |  |

### <a id="consent_for_sharing"></a>Consent for data sharing (`consent_for_sharing`)

What participants (or the approved waiver) allow regarding sharing data beyond the research team.

| Code | Label | ERIC descriptors |
|---|---|---|
| `broad_sharing` | Broad sharing of de-identified data consented |  |
| `restricted_sharing` | Sharing only under restrictions (e.g., approved researchers, data-use agreement) |  |
| `no_sharing` | No sharing beyond the research team |  |
| `not_addressed` | Consent did not address sharing |  |
| `not_applicable` | Not applicable (no human-subjects data) |  |

### <a id="identifiability"></a>Identifiability (`identifiability`)

Identifiability of the data in this resource.

| Code | Label | ERIC descriptors |
|---|---|---|
| `identifiable` | Identifiable |  |
| `coded` | Coded / pseudonymous (a linking key exists) |  |
| `deidentified` | De-identified |  |
| `anonymous` | Anonymous (never linked to identity) |  |
| `aggregate_only` | Aggregate statistics only |  |
| `synthetic` | Synthetic |  |
| `not_applicable` | Not applicable (no participant data) |  |

### <a id="sensitivity_flag"></a>Sensitivity flags (`sensitivity_flag`)

Kinds of sensitive information present in the underlying data.

| Code | Label | ERIC descriptors |
|---|---|---|
| `direct_identifiers` | Direct identifiers | Privacy |
| `indirect_identifiers` | Indirect identifiers or small groups | Privacy |
| `sensitive_information` | Sensitive personal information | Confidentiality |
| `education_records` | Education records (FERPA) | Student Records (unverified), Privacy |

### <a id="access_level"></a>Access level (`access_level`)

How the data in or described by this resource can be accessed.

| Code | Label | ERIC descriptors |
|---|---|---|
| `open` | Open (public) |  |
| `registered` | Registered users |  |
| `controlled` | Controlled access (application and/or data-use agreement) |  |
| `closed` | Closed (research team only) |  |
| `metadata_only` | Metadata only (data not shared) |  |

### <a id="indigenous_data"></a>Indigenous data (`indigenous_data`)

Whether the resource contains or derives from data about Indigenous Peoples, nations, communities, lands, territories, or knowledges.

| Code | Label | ERIC descriptors |
|---|---|---|
| `yes` | Yes | Indigenous Populations |
| `no` | No |  |
| `unknown` | Unknown / not yet assessed |  |

### <a id="indigenous_governance"></a>Indigenous data governance (`indigenous_governance`)

How Indigenous authority to control the data (CARE: Authority to control) is exercised.

| Code | Label | ERIC descriptors |
|---|---|---|
| `community_agreement` | Data governance agreement with the community or nation |  |
| `tribal_review` | Tribal or Indigenous research review approval |  |
| `consultation_ongoing` | Consultation in progress |  |
| `none` | No governance arrangement |  |
| `not_applicable` | Not applicable |  |

### <a id="constructs"></a>Constructs

Defined in [`library/constructs.json`](../../library/constructs.json).

| Code | Label | Definition | ERIC descriptors |
|---|---|---|---|
| `conceptual_understanding` | Conceptual understanding | Grasp of core disciplinary ideas and the ability to apply them to new situations, as distinct from recall or procedural skill. | Scientific Concepts, Misconceptions, Concept Formation |
| `content_knowledge` | Content knowledge | Factual and procedural knowledge of a subject area, as typically measured by course exams or knowledge tests. | Knowledge Level, Academic Achievement |
| `problem_solving` | Problem solving | Approaches and skill in working through unfamiliar disciplinary problems, including planning, representation and checking. | Problem Solving |
| `scientific_reasoning` | Scientific reasoning | Reasoning about evidence, variables, models and experiments, including control of variables and proportional reasoning. | Science Process Skills, Scientific Literacy |
| `quantitative_reasoning` | Quantitative reasoning | Using numbers, graphs and mathematical relationships to make sense of disciplinary situations. | Numeracy, Mathematical Logic |
| `self_efficacy` | Self-efficacy | A person's belief in their capability to succeed at specific tasks or in a specific domain. | Self Efficacy |
| `perceived_behavioral_control` | Perceived behavioral control | Perceived ease or difficulty of performing a behavior, including access to needed resources (Theory of Planned Behavior). | Locus of Control |
| `interest` | Interest | Enjoyment of and desire to engage with a subject, either in the moment (situational) or as an enduring disposition (individual). | Student Interests (unverified) |
| `task_value` | Task value | How interesting, important and useful a person judges a subject or task to be, and what it costs them to engage. | Values, Expectation |
| `goal_orientation` | Goal orientation | The reasons a learner pursues academic tasks, such as mastering material versus demonstrating ability or earning grades. | Goal Orientation |
| `anxiety` | Academic anxiety | Worry and emotional arousal related to a subject or to evaluation within it. | Anxiety, Test Anxiety, Mathematics Anxiety |
| `attitude_toward_subject` | Attitude toward the subject or behavior | Overall positive or negative evaluation of a subject, activity or behavior. | Scientific Attitudes, Student Attitudes (unverified) |
| `behavioral_intention` | Behavioral intention | Stated readiness or plan to perform a behavior, such as taking further courses or pursuing a major or career. | Intention, Academic Persistence |
| `mindset` | Mindset / beliefs about ability | Beliefs about whether ability in a domain is fixed or can be developed, and about who can succeed. | Beliefs, Self Concept |
| `sense_of_belonging` | Sense of belonging | Feeling accepted, valued and included as a member of a course, discipline, institution or community. | Sense of Belonging |
| `disciplinary_identity` | Disciplinary identity | Seeing oneself, and being recognized by others, as the kind of person who does a discipline (e.g. a physics person, a scientist). | Professional Identity, Identification (Psychology) |
| `subjective_norm` | Subjective norm | Perceived expectations from important others about whether one should perform a behavior. | Social Influences, Peer Influence |
| `stereotype_perception` | Perceived stereotypes and climate | Awareness of stereotypes about who belongs or succeeds in a field, and perception of bias in the learning environment. | Stereotypes (unverified), Educational Environment |
| `community_connectedness` | Classroom community | Perceived cohesion, trust and mutual support among learners and instructors in a learning setting. | Sense of Community |
| `epistemological_beliefs` | Beliefs about the discipline and learning it | Beliefs about the nature of disciplinary knowledge and about what learning the discipline involves, often compared with expert views. | Epistemology, Beliefs |
| `nature_of_science` | Understanding of the nature of science | Understanding of how scientific knowledge is generated, justified and revised. | Scientific Literacy, Epistemology |
| `real_world_relevance` | Perceived real-world relevance | Seeing connections between disciplinary content and everyday life or societal issues. | Relevance (Education) |
| `self_regulated_learning` | Self-regulated learning | Planning, monitoring and adjusting one's own learning, including metacognition and management of time and effort. | Metacognition, Self Management |
| `learning_strategies` | Study and learning strategies | Specific cognitive and resource-management strategies used when studying, such as rehearsal, elaboration, organization and help seeking. | Learning Strategies, Study Habits (unverified) |
| `engagement` | Engagement | Behavioral, cognitive and emotional involvement in learning activities. | Learner Engagement |
| `critical_thinking` | Critical thinking | Evaluating claims, evidence and arguments and applying prior knowledge to new problems. | Critical Thinking (unverified) |
| `teaching_practices` | Teaching practices | What instructors do during instruction, such as lecturing, posing questions, facilitating group work or giving feedback. | Teaching Methods |
| `student_classroom_activity` | Student classroom activity | What students are observed doing during instruction, such as listening, discussing, working in groups or answering questions. | Classroom Observation Techniques, Student Behavior (unverified) |
| `reformed_teaching` | Reformed / student-centered teaching | Degree to which instruction is inquiry-oriented and student-centered rather than transmission-oriented. | Active Learning, Inquiry, Student Centered Learning (unverified) |
| `teaching_beliefs` | Instructor beliefs about teaching | Instructors' beliefs about how students learn and what effective teaching looks like. | Teacher Attitudes, Beliefs |
| `learning_environment` | Learning environment perceptions | Learners' perceptions of course structure, support, fairness and climate. | Classroom Environment, Educational Environment |
