# HuMeta: elements and vocabularies

*HuMeta: The Social Science, Humanities, and Education Study Metadata Profile*

Version 1.0.0-draft.1 (draft). Generated from `profile.json` and `vocabularies.json` by `scripts/build_profile_artifacts.py`; do not edit by hand.

Obligations: **M** = Mandatory: every record must have it.; **MA** = Mandatory if applicable: required when the stated condition holds.; **R** = Recommended.; **O** = Optional.

Alignments: each element lists the standards it corresponds to. No mark = exact match; **≈** = close match; **~** = related. `HuMeta` = defined by this profile, with no equivalent in a general-purpose standard. *(expert input wanted)* = we are seeking expert input on this alignment. Full list, with notes, in [`crosswalks/alignments.csv`](crosswalks/alignments.csv).

Standards: [HuMeta](https://github.com/JLib271/humeta-profile/blob/main/README.md) = HuMeta profile (element or vocabulary defined by this profile); [DataCite](https://schema.datacite.org/) = DataCite Metadata Schema 4.7; [DC](https://www.dublincore.org/specifications/dublin-core/dcmi-terms/) = Dublin Core (DCMI Metadata Terms); [schema.org](https://schema.org/Dataset) = schema.org Dataset; [ERIC](https://eric.ed.gov/?ti=all) = ERIC Thesaurus; [DDI-C](https://ddialliance.org/Specification/DDI-Codebook/2.5/) = DDI-Codebook 2.5 (Data Documentation Initiative); [DDI CV](https://rdf-vocabulary.ddialliance.org/) = DDI Alliance Controlled Vocabularies (CC BY 4.0); [OECD FOS](http://www.oecd.org/science/inno/38235147.pdf) = OECD Fields of Science and Technology (FOS), as used by DataCite; [ORCID](https://orcid.org/) = ORCID iD; [SPDX](https://spdx.org/licenses/) = SPDX License List; [BCP 47](https://www.rfc-editor.org/info/bcp47) = IETF BCP 47 language tags; [ISO 3166](https://www.iso.org/iso-3166-country-codes.html) = ISO 3166-1 alpha-2 country codes; [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) = ISO 8601 dates; [NCES](https://nces.ed.gov/programs/edge/Geographic/LocaleBoundaries) = NCES locale classification (locale types City, Suburb, Town, Rural); [ISCED](https://uis.unesco.org/sites/default/files/documents/international-standard-classification-of-education-isced-2011-en.pdf) = UNESCO International Standard Classification of Education (ISCED 2011); [AERA/APA/NCME](https://www.testingstandards.net/) = Standards for Educational and Psychological Testing (2014); [Common Rule](https://www.hhs.gov/ohrp/regulations-and-policy/regulations/45-cfr-46/) = US Common Rule for human-subjects research (45 CFR 46); [FERPA](https://studentprivacy.ed.gov/) = Family Educational Rights and Privacy Act (34 CFR Part 99); [CARE](https://www.gida-global.org/care) = CARE Principles for Indigenous Data Governance; [Local Contexts](https://localcontexts.org/) = Local Contexts Traditional Knowledge and Biocultural Labels and Notices; [RightsStatements](https://rightsstatements.org/) = RightsStatements.org rights statements; [AoIR IRE 3.0](https://aoir.org/reports/ethics3.pdf) = Association of Internet Researchers, Internet Research: Ethical Guidelines 3.0 (2019); [TaDiRAH](https://vocabs.dariah.eu/tadirah/) = TaDiRAH 2.0.3: Taxonomy of Digital Research Activities in the Humanities (DARIAH, CC0); [TEI](https://tei-c.org/guidelines/p5/) = TEI P5 Guidelines (Text Encoding Initiative); [ISO 639](https://www.loc.gov/standards/iso639-2/php/code_list.php) = ISO 639 language codes (as used in BCP 47); [ANZSRC FoR](https://linked.data.gov.au/def/anzsrc-for/2020) = Australian and New Zealand Standard Research Classification 2020: Fields of Research (ABS and Stats NZ)

Modules: the **core** applies to every record; a field module (such as **Education**) applies only when a record includes it, and its mandatory elements are mandatory only then.

## Core elements

Elements for any study in the social sciences, humanities, or education.

| Element | Obligation | Cardinality | Definition | Aligned with | DataCite 4.7 mapping |
|---|---|---|---|---|---|
| <a id="resource.title"></a>`resource.title` | M | 1 | Name of the resource. | `DataCite: titles.title`, `DC: title`, `schema.org: name`, `DDI-C: titl` | titles.title |
| <a id="resource.creators"></a>`resource.creators` | M | 1..n | People or organizations primarily responsible for the resource, with ORCID iDs where available. | `DataCite: creators`, `DC: creator`, `schema.org: creator`, `ORCID: ORCID iD (nameIdentifier)`, `DDI-C: AuthEnty` | creators (nameIdentifier with nameIdentifierScheme ORCID; affiliation) |
| <a id="resource.publisher"></a>`resource.publisher` | M | 1 | Entity that holds, archives, or makes the resource available (usually the repository or institution). | `DataCite: publisher`, `DC: publisher`, `schema.org: publisher`, `≈DDI-C: distrbtr` | publisher |
| <a id="resource.publication_year"></a>`resource.publication_year` | M | 1 | Year the resource was or will be made publicly available. | `DataCite: publicationYear`, `≈DC: issued`, `≈schema.org: datePublished`, `≈DDI-C: distDate` | publicationYear |
| <a id="resource.resource_type"></a>`resource.resource_type` | M | 1 | General type of the resource, using DataCite resourceTypeGeneral values. | `DataCite: resourceTypeGeneral`, `≈DC: type`, `≈schema.org: @type` | types.resourceTypeGeneral; types.resourceType = 'HuMeta <type>' |
| <a id="resource.identifier"></a>`resource.identifier` | O | 0..1 | Persistent identifier (DOI preferred) once one has been assigned. | `DataCite: identifier`, `DC: identifier`, `schema.org: identifier`, `DDI-C: IDNo` | identifiers (DOI) or alternateIdentifiers |
| <a id="resource.description"></a>`resource.description` | R | 0..1 | Abstract or summary of the resource. | `DataCite: description (Abstract)`, `DC: abstract`, `schema.org: description`, `DDI-C: abstract` | descriptions (descriptionType Abstract) |
| <a id="resource.keywords"></a>`resource.keywords` | O | 0..n | Free-text keywords. | `DataCite: subject (no scheme)`, `≈DC: subject`, `schema.org: keywords`, `DDI-C: keyword` | subjects (no scheme) |
| <a id="resource.language"></a>`resource.language` | R | 0..1 | Primary language of the resource (BCP 47 code, e.g. en). | `DataCite: language`, `DC: language`, `schema.org: inLanguage`, `BCP 47: language tag` | language |
| <a id="resource.license"></a>`resource.license` | R | 0..1 | License for the resource, as an SPDX identifier where possible (e.g. CC-BY-4.0). | `DataCite: rightsList`, `DC: license`, `schema.org: license`, `SPDX: license identifier` | rightsList (rightsIdentifier, rightsIdentifierScheme SPDX) |
| <a id="resource.funding"></a>`resource.funding` | O | 0..n | Funders and award numbers. | `DataCite: fundingReferences`, `≈schema.org: funder`, `DDI-C: fundAg / grantNo` | fundingReferences |
| <a id="resource.collection_dates"></a>`resource.collection_dates` | R | 0..1 | Start and end of data collection (ISO 8601 dates). | `DataCite: date (Collected)`, `ISO 8601: date`, `~DC: temporal`, `~schema.org: temporalCoverage`, `DDI-C: collDate` | dates (dateType Collected, as start/end) |
| <a id="resource.geography"></a>`resource.geography` | R | 0..1 | Countries (ISO 3166-1 alpha-2) and, for the US, states (USPS codes) where data were collected. | `DataCite: geoLocationPlace`, `ISO 3166: country code`, `≈DC: spatial`, `≈schema.org: spatialCoverage`, `≈DDI-C: nation / geogCover` | geoLocations (geoLocationPlace) |
| <a id="resource.related"></a>`resource.related` | O | 0..n | Related publications, datasets, preregistrations, or instruments, with a DataCite relationType. | `DataCite: relatedIdentifiers`, `≈DC: relation`, `~schema.org: citation` | relatedIdentifiers |
| <a id="study.fields"></a>`study.fields` | M | 1..n | Broad field(s) the study belongs to: education, social sciences, humanities, arts, or other. Interdisciplinary studies choose several. Vocabulary: [research_field](#research_field). | `HuMeta`, `OECD FOS: category`, `DataCite: subject (FOS scheme)`, `≈DDI-C: topcClas` | subjects (subjectScheme 'Fields of Science and Technology (FOS)', e.g. 'FOS: Educational sciences') |
| <a id="study.design.topic"></a>`study.design.topic` | R | 0..1 | The main subject or topic of the study, in the researcher's words (e.g., 'introductory geology lab learning'). | `HuMeta`, `≈DataCite: subject`, `≈DC: subject`, `≈schema.org: about` | subjects (no scheme) |
| <a id="study.design.research_questions"></a>`study.design.research_questions` | R | 0..1 | Primary research questions, objectives, or hypotheses. | `HuMeta`, `≈DataCite: description (Methods)`, `~DC: description` | descriptions (descriptionType Methods) |
| <a id="study.design.frameworks"></a>`study.design.frameworks` | R | 0..n | Theories, theoretical lenses, or framework approaches (including the researcher's own framework, or an exploratory approach with no framework chosen in advance) that guide the study, from the HuMeta framework list (library/frameworks.json). | `HuMeta`, `≈DataCite: subject (scheme)`, `~schema.org: about` | subjects (subjectScheme 'HuMeta Frameworks', valueURI per framework); descriptions (Methods) |
| <a id="study.design.framework_description"></a>`study.design.framework_description` | O | 0..1 | How the framework guides the study, or a description of the researcher's own framework or lens. | `HuMeta`, `≈DataCite: description (Methods)` | descriptions (descriptionType Methods) |
| <a id="study.design.unit_of_analysis"></a>`study.design.unit_of_analysis` | O | 0..n | The unit(s) the analysis is about: people, groups, places, texts, images, objects, and so on. Vocabulary: [unit_of_analysis](#unit_of_analysis). | `HuMeta`, `DDI CV: AnalysisUnit 2.1.3`, `DDI-C: anlyUnit`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'HuMeta Units of Analysis') |
| <a id="study.design.sampling_procedure"></a>`study.design.sampling_procedure` | O | 0..n | How cases (people, texts, objects, sites) were selected. Vocabulary: [sampling_procedure](#sampling_procedure). | `HuMeta`, `DDI CV: SamplingProcedure 2.0.2`, `DDI-C: sampProc`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'HuMeta Sampling Procedures'); descriptions (Methods) |
| <a id="study.constructs"></a>`study.constructs` | MA | 0..n | Constructs measured, from the HuMeta construct vocabulary (library/constructs.json), optionally with the instrument, version and subscale used. *Mandatory when resource_type is Dataset or Instrument.* | `HuMeta`, `≈ERIC: descriptors`, `≈schema.org: variableMeasured`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'HuMeta Constructs', valueURI per construct); for datasets, relatedIdentifiers to the instrument's library record (URL, relationType IsCollectedBy) and its publication (DOI, relationType References); ERIC descriptors as additional subjects |
| <a id="study.discipline"></a>`study.discipline` | R | 0..n | Discipline(s) or subject area(s) the study is about; for education studies, also the subject taught or learned. Chosen from the ANZSRC 2020 Fields of Research (divisions and groups). Vocabulary: [discipline](#discipline). | `ANZSRC FoR: Fields of Research 2020 (divisions and groups)`, `≈OECD FOS: subcategory (per term)`, `≈ERIC: descriptors`, `≈DC: subject`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'ANZSRC Fields of Research', valueURI and classificationCode per term), plus the corresponding OECD Fields of Science subject (subjectScheme 'Fields of Science and Technology (FOS)') |
| <a id="study.population.human_participants"></a>`study.population.human_participants` | M | 1 | Whether people take part in the study directly, are its subject only indirectly (records, public posts), or are not involved (texts, artworks, objects only). Vocabulary: [human_participants](#human_participants). | `HuMeta`, `~Common Rule: "human subject" definition` | descriptions (Methods) |
| <a id="study.population.participant_roles"></a>`study.population.participant_roles` | MA | 0..n | Who the participants, or the people the data are about, are. *Mandatory when human participants is direct or indirect.* Vocabulary: [participant_role](#participant_role). | `HuMeta`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'HuMeta Participant Roles') |
| <a id="study.population.description"></a>`study.population.description` | R | 0..1 | Narrative description of the participants and sampling, without identifying information. | `HuMeta`, `≈DataCite: description (Methods)`, `≈DDI-C: universe` | descriptions (descriptionType Methods) |
| <a id="study.population.sample_size"></a>`study.population.sample_size` | R | 0..1 | Number of participants (or units) in the data. | `HuMeta`, `≈DataCite: sizes` | sizes ('N = <n> participants') |
| <a id="study.context.locale"></a>`study.context.locale` | R | 0..n | Community type(s) where the study took place. Vocabulary: [locale](#locale). | `HuMeta`, `NCES: locale type`, `≈ERIC: descriptors` | subjects (subjectScheme 'HuMeta Locales') |
| <a id="study.evidence.study_designs"></a>`study.evidence.study_designs` | MA | 0..n | Design(s) that produced the evidence. *Mandatory when resource_type is Dataset or StudyRegistration.* Vocabulary: [study_design](#study_design). | `HuMeta`, `≈ERIC: descriptors`, `≈DataCite: description (Methods)`, `~DDI CV: TimeMethod 1.2.3 (time-related designs)`, `~DDI-C: timeMeth` | subjects (subjectScheme 'HuMeta Study Designs'); descriptions (Methods) |
| <a id="study.evidence.measurement_evidence"></a>`study.evidence.measurement_evidence` | O | 0..n | Kinds of reliability and validity evidence the resource provides. Optional and not asked in the portal's study profile; an instrument's measurement evidence is recorded with the instrument in the HuMeta instrument library. *Mandatory when resource_type is Instrument.* Vocabulary: [measurement_evidence](#measurement_evidence). | `HuMeta`, `≈AERA/APA/NCME: sources of validity evidence`, `≈ERIC: descriptors` | subjects (subjectScheme 'HuMeta Measurement Evidence') |
| <a id="study.evidence.data_collection_methods"></a>`study.evidence.data_collection_methods` | R | 0..n | How data or sources were gathered. Vocabulary: [data_collection_method](#data_collection_method). | `HuMeta`, `≈DDI CV: ModeOfCollection 5.0.1`, `DDI-C: collMode`, `≈ERIC: descriptors`, `≈schema.org: measurementTechnique` | subjects (subjectScheme 'HuMeta Data Collection Methods') |
| <a id="study.evidence.analysis_methods"></a>`study.evidence.analysis_methods` | R | 0..n | How the data or sources were analyzed: statistical, qualitative, interpretive, or computational. Vocabulary: [analysis_method](#analysis_method). | `HuMeta`, `≈DataCite: description (Methods)`, `≈ERIC: descriptors` | subjects (subjectScheme 'HuMeta Analysis Methods'); descriptions (Methods) |
| <a id="study.sources.types"></a>`study.sources.types` | MA | 0..n | Kinds of sources studied other than data collected from participants: texts, archival records, images, artworks, media, online content, objects, existing datasets. *Mandatory when human participants is none.* Vocabulary: [source_type](#source_type). | `HuMeta`, `≈DDI CV: GeneralDataFormat 2.0.3 / DataSourceType 1.0.2`, `~DDI-C: dataKind`, `≈DC: type` | subjects (subjectScheme 'HuMeta Source Types') |
| <a id="study.sources.description"></a>`study.sources.description` | R | 0..1 | The corpus, collection, or set of sources: what it includes and how it was selected. | `HuMeta`, `≈DDI-C: dataSrc`, `~DC: source`, `≈DataCite: description (Methods)` | descriptions (descriptionType Methods) |
| <a id="study.sources.holdings"></a>`study.sources.holdings` | O | 0..1 | Where the sources are held: archives, libraries, museums, collections, or platforms. | `HuMeta`, `~DDI-C: srcOrig` | descriptions (descriptionType Methods) |
| <a id="study.sources.time_period"></a>`study.sources.time_period` | O | 0..1 | The period the sources cover or were created in (e.g., 1850-1900, 19th century), as distinct from when data were collected. | `HuMeta`, `DC: temporal`, `DDI-C: timePrd`, `schema.org: temporalCoverage`, `DataCite: date (Coverage)` | dates (dateType Coverage) |
| <a id="study.sources.rights"></a>`study.sources.rights` | R | 0..1 | Copyright or other rights status of the sources, which decides whether copies of them can be shared. Vocabulary: [source_rights](#source_rights). | `HuMeta`, `~RightsStatements: rights statement`, `≈DC: rights`, `~DataCite: rightsList` | rightsList (rights statement for sources) |
| <a id="study.ethics.human_subjects_review"></a>`study.ethics.human_subjects_review` | M | 1 | Ethics / IRB review status, as reported by the researcher. Vocabulary: [human_subjects_review](#human_subjects_review). | `HuMeta`, `~Common Rule: IRB review / exemption` | descriptions (descriptionType Other, 'Ethics and access') |
| <a id="study.ethics.consent"></a>`study.ethics.consent` | R | 0..1 | How participants agreed to take part. Vocabulary: [consent](#consent). | `HuMeta`, `~Common Rule: informed consent / waiver` | descriptions (Other, 'Ethics and access') |
| <a id="study.ethics.consent_for_sharing"></a>`study.ethics.consent_for_sharing` | M | 1 | What participants allow regarding sharing beyond the research team. Vocabulary: [consent_for_sharing](#consent_for_sharing). | `HuMeta`, `~schema.org: conditionsOfAccess`, `~DataCite: rightsList` | descriptions (Other, 'Ethics and access'); rightsList |
| <a id="study.ethics.identifiability"></a>`study.ethics.identifiability` | M | 1 | Identifiability of the data. Vocabulary: [identifiability](#identifiability). | `HuMeta`, `~FERPA: de-identified records`, `~DDI-C: confDec` | descriptions (Other, 'Ethics and access') |
| <a id="study.ethics.sensitivity_flags"></a>`study.ethics.sensitivity_flags` | R | 0..n | Kinds of sensitive information in the underlying data. Vocabulary: [sensitivity_flag](#sensitivity_flag). | `HuMeta`, `≈FERPA: education records` | descriptions (Other, 'Ethics and access') |
| <a id="study.ethics.online_data"></a>`study.ethics.online_data` | MA | 0..n | How content from websites, social media, or other platforms was collected and handled: public or private spaces, platform terms, consent, and protection of authors. *Mandatory when the study uses social media or website sources, or web or platform data collection.* Vocabulary: [online_data_practice](#online_data_practice). | `HuMeta`, `~AoIR IRE 3.0: ethical guidance` | descriptions (descriptionType Other, ethics statement) |
| <a id="study.ethics.access_level"></a>`study.ethics.access_level` | M | 1 | How the data can be accessed. Vocabulary: [access_level](#access_level). | `HuMeta`, `≈DC: accessRights`, `≈schema.org: conditionsOfAccess`, `≈DataCite: rightsList`, `≈DDI-C: restrctn` | rightsList (access statement) |
| <a id="study.ethics.governance_notes"></a>`study.ethics.governance_notes` | O | 0..1 | Approval references, data-use restrictions, retention or de-identification requirements (no confidential details). | `HuMeta`, `~DC: accessRights`, `≈DataCite: description (Other)` | descriptions (Other, 'Ethics and access') |
| <a id="study.care.indigenous_data"></a>`study.care.indigenous_data` | M | 1 | Whether the resource contains or derives from data about Indigenous Peoples, nations, communities, lands, territories, or knowledges. Vocabulary: [indigenous_data](#indigenous_data). | `HuMeta`, `≈CARE: scope: Indigenous data` | descriptions (Other, 'CARE statement') |
| <a id="study.care.governance"></a>`study.care.governance` | MA | 0..1 | How Indigenous authority to control the data is exercised (CARE: Authority to control). *Mandatory when indigenous_data is yes.* Vocabulary: [indigenous_governance](#indigenous_governance). | `HuMeta`, `≈CARE: Authority to control` | descriptions (Other, 'CARE statement'); rightsList |
| <a id="study.care.statement"></a>`study.care.statement` | MA | 0..1 | How the work provides collective benefit, respects authority to control, and meets responsibility and ethics obligations to the communities involved. *Mandatory when indigenous_data is yes.* | `HuMeta`, `≈CARE: Collective benefit; Responsibility; Ethics`, `≈DataCite: description (Other)` | descriptions (Other, 'CARE statement') |
| <a id="study.care.local_contexts_project"></a>`study.care.local_contexts_project` | O | 0..1 | URL of a Local Contexts Hub project holding Traditional Knowledge or Biocultural Labels or Notices for this resource. | `Local Contexts: Hub project`, `≈DataCite: relatedIdentifier` | relatedIdentifiers (relatedIdentifierType URL, relationType IsDescribedBy) |
| <a id="study.care.local_contexts_labels"></a>`study.care.local_contexts_labels` | O | 0..n | Names of Local Contexts Labels or Notices applied by the community (e.g. 'TK Attribution'). | `Local Contexts: TK/BC Labels and Notices` | descriptions (Other, 'CARE statement') |

## Education module

Optional module for studies in education settings: learners' education levels, institutions and instructional settings. Its mandatory elements apply only when a record includes the module.

| Element | Obligation | Cardinality | Definition | Aligned with | DataCite 4.7 mapping |
|---|---|---|---|---|---|
| <a id="education.education_levels"></a>`education.education_levels` | M | 1..n | Education level(s) of the participants. Vocabulary: [education_level](#education_level). | `HuMeta`, `ISCED: levels of education 0–8`, `≈ERIC: education level descriptors`, `≈DC: educationLevel` (expert input wanted) `≈schema.org: educationalLevel` (expert input wanted) | subjects (subjectScheme 'HuMeta Education Levels'); ISCED 2011 level as an additional subject (subjectScheme 'ISCED 2011') |
| <a id="education.undergraduate_levels"></a>`education.undergraduate_levels` | O | 0..n | Course level(s) for undergraduate studies. Vocabulary: [undergraduate_level](#undergraduate_level). | `HuMeta`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'HuMeta Undergraduate Levels') |
| <a id="education.institution_types"></a>`education.institution_types` | R | 0..n | Type(s) of institution or organization. Vocabulary: [institution_type](#institution_type). | `HuMeta`, `≈ERIC: descriptors` | subjects (subjectScheme 'HuMeta Institution Types') |
| <a id="education.modality"></a>`education.modality` | R | 0..n | How instruction or participation was delivered. Vocabulary: [modality](#modality). | `HuMeta`, `≈ERIC: descriptors` | subjects (subjectScheme 'HuMeta Modalities') |
| <a id="education.learning_environments"></a>`education.learning_environments` | R | 0..n | Instructional setting(s). Vocabulary: [learning_environment](#learning_environment). | `HuMeta`, `≈ERIC: descriptors` | subjects (subjectScheme 'HuMeta Learning Environments') |
| <a id="education.pedagogy"></a>`education.pedagogy` | O | 0..n | Instructional approach(es) used or studied. Vocabulary: [pedagogy](#pedagogy). | `HuMeta`, `≈ERIC: descriptors`, `≈DC: instructionalMethod` (expert input wanted) | subjects (subjectScheme 'HuMeta Instructional Approaches') |

## Social Science module

Optional module for social science studies. The social sciences already have a full metadata standard, DDI (Data Documentation Initiative), used by ICPSR, CESSDA archives, the UK Data Service, and Dataverse. This module does not replace it: it records a few study-level details using DDI-Codebook's own elements and links to the study's full DDI documentation. What HuMeta adds is the link from constructs and measures to theory (Module 2).

| Element | Obligation | Cardinality | Definition | Aligned with | DataCite 4.7 mapping |
|---|---|---|---|---|---|
| <a id="social_science.kind_of_data"></a>`social_science.kind_of_data` | O | 0..1 | Whether the data are quantitative, qualitative, or mixed. Vocabulary: [kind_of_data](#kind_of_data). | `DDI CV: KindOfData 1.0.0`, `DDI-C: dataKind` | descriptions (descriptionType Methods) |
| <a id="social_science.universe"></a>`social_science.universe` | O | 0..1 | The group of people, organizations, or other units the findings are meant to describe, including who is excluded (e.g., adults 18 and older living in private households in Michigan). | `DDI-C: universe` | descriptions (descriptionType Methods) |
| <a id="social_science.geographic_unit"></a>`social_science.geographic_unit` | O | 0..1 | The lowest level of geography the data identify (e.g., country, state, county, school district, census tract). | `DDI-C: geogUnit` | descriptions (descriptionType Methods) |
| <a id="social_science.response_rate"></a>`social_science.response_rate` | O | 0..1 | The share of sampled units that provided data, with how it was calculated (e.g., AAPOR RR3 = 41%). | `DDI-C: respRate` | descriptions (descriptionType Methods) |
| <a id="social_science.weighting"></a>`social_science.weighting` | O | 0..1 | Whether the data include weights, what they adjust for, and which variable holds them. | `DDI-C: weight` | descriptions (descriptionType Methods) |
| <a id="social_science.ddi_record"></a>`social_science.ddi_record` | O | 0..1 | Link to the study's full documentation in DDI (DDI-Codebook or DDI-Lifecycle), for example its page at ICPSR, the CESSDA Data Catalogue, the UK Data Service, or a Dataverse. DDI is the place for variable-, question-, and sampling-level detail. | `~DDI-C: codeBook (the study's DDI record)`, `≈DataCite: relatedIdentifier` | relatedIdentifiers (relatedIdentifierType URL, relationType IsDocumentedBy) |

## Arts and Humanities module

Optional module for studies in the arts and humanities: research activities (TaDiRAH), the works, creators, or objects studied, the languages of the sources, and editorial or encoding standards. Sources, their time period, holdings, and rights are in the core.

| Element | Obligation | Cardinality | Definition | Aligned with | DataCite 4.7 mapping |
|---|---|---|---|---|---|
| <a id="humanities.research_activities"></a>`humanities.research_activities` | O | 0..n | The research activities the study involves, from TaDiRAH, the Taxonomy of Digital Research Activities in the Humanities. Vocabulary: [tadirah_activity](#tadirah_activity). | `TaDiRAH: concepts (version 2.0.3)`, `≈DataCite: subject (scheme)` | subjects (subjectScheme 'TaDiRAH', valueURI per concept) |
| <a id="humanities.objects_of_study"></a>`humanities.objects_of_study` | O | 0..1 | The works, people, collections, artifacts, performances, or other objects the study examines (e.g., the letters of Zitkála-Šá; Detroit murals of the 1930s). | `≈DC: subject`, `≈schema.org: about`, `≈DataCite: subject` | subjects |
| <a id="humanities.source_languages"></a>`humanities.source_languages` | O | 0..n | Languages of the sources studied (ISO 639 or BCP 47 codes, e.g., fr, la, nv), as distinct from the language of this resource. | `~DC: language (of the sources)`, `ISO 639: language code` | descriptions (descriptionType Methods) |
| <a id="humanities.editorial_standards"></a>`humanities.editorial_standards` | O | 0..1 | Standards or conventions used to transcribe, edit, encode, or image the sources (e.g., TEI P5, IIIF, a documentary-editing style guide). | `≈TEI: encodingDesc / editorialDecl` | descriptions (descriptionType Methods) |

## Rules

| Rule | Severity | Requirement |
|---|---|---|
| R1 | error | Instruments, and datasets from studies with human participants, must list at least one construct measured. |
| R2 | error | Datasets and study registrations must list at least one study design. |
| R4 | error | Open access requires data that are de-identified, anonymous, aggregate-only, synthetic, or not participant data. |
| R5 | error | Open access requires consent for broad sharing (or no human-subjects data). |
| R6 | error | Data cannot be open or registered-access while human-subjects review is 'not yet assessed' or 'pending'. |
| R7 | error | Indigenous data require a governance arrangement and a CARE statement. |
| R8 | error | Indigenous data may be open only under a community data governance agreement or tribal review approval. |
| R9 | warning | Data from education records (FERPA): confirm the institution's FERPA review before any sharing. |
| R10 | warning | Indigenous data status is unknown; assess it before sharing. |
| R11 | warning | A specific community or a tribal college is involved; confirm whether the data are Indigenous data. |
| R12 | warning | Direct identifiers are flagged; they must be removed before the data are shared. |
| R13 | warning | Public online posts can identify their authors through search even after names are removed. Before sharing, remove usernames and alter quotes, or share only post IDs. |
| R14 | warning | Confirm that collecting and sharing online content follows the platform's terms of service or a data-access agreement. |
| R15 | warning | Online content may come from minors; review whether it can be shared, and with whom. |
| R16 | warning | Content from closed or semi-private online spaces usually needs authors' consent or ethics-review approval, because users there expect privacy. |
| R17 | warning | Sources are in copyright or not yet evaluated: share metadata, citations, or derived data rather than copies unless the rights allow it. |

## Vocabularies

### <a id="research_field"></a>Research field (`research_field`)

Broad field(s) the study belongs to. Choose all that apply; interdisciplinary studies choose several. Mapped to the OECD Fields of Science and Technology (FOS) used by DataCite.

| Code | Label | ERIC descriptors |
|---|---|---|
| `education` | Education | Educational Research |
| `social_sciences` | Social sciences (including psychology, communication, economics, sociology) |  |
| `humanities` | Humanities (including history, languages and literature, philosophy, religion) |  |
| `arts` | Arts (visual arts, performing arts, music, design, art history) |  |
| `other_field` | Other field (e.g., natural sciences, health, engineering) |  |

### <a id="discipline"></a>Discipline or subject area (`discipline`)

Discipline(s) or subject area(s) the study is about; for education studies, also the subject taught or learned. Terms are the Divisions (broad) and Groups of the Australian and New Zealand Standard Research Classification (ANZSRC) 2020 Fields of Research. Based on Australian Bureau of Statistics and Stats NZ material, (c) Commonwealth of Australia and Crown Copyright New Zealand 2020, used under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/); HuMeta added the OECD FOS mapping and '(all)' division labels (see THIRD_PARTY_NOTICES.md). 'anzsrc' is the FoR code (concept URI https://linked.data.gov.au/def/anzsrc-for/2020/<code>); 'fos' is the corresponding OECD Fields of Science code used for DataCite. Terms marked deprecated are the profile's earlier discipline list; records using them are moved to the terms in replaced_by.

| Code | Label | ERIC descriptors |
|---|---|---|
| `anzsrc_30` | Agricultural, veterinary and food sciences (all) |  |
| `anzsrc_3001` | Agricultural biotechnology |  |
| `anzsrc_3002` | Agriculture, land and farm management |  |
| `anzsrc_3003` | Animal production |  |
| `anzsrc_3004` | Crop and pasture production |  |
| `anzsrc_3005` | Fisheries sciences |  |
| `anzsrc_3006` | Food sciences |  |
| `anzsrc_3007` | Forestry sciences |  |
| `anzsrc_3008` | Horticultural production |  |
| `anzsrc_3009` | Veterinary sciences |  |
| `anzsrc_3099` | Other agricultural, veterinary and food sciences |  |
| `anzsrc_31` | Biological sciences (all) | Biology |
| `anzsrc_3101` | Biochemistry and cell biology |  |
| `anzsrc_3102` | Bioinformatics and computational biology |  |
| `anzsrc_3103` | Ecology |  |
| `anzsrc_3104` | Evolutionary biology |  |
| `anzsrc_3105` | Genetics |  |
| `anzsrc_3106` | Industrial biotechnology |  |
| `anzsrc_3107` | Microbiology |  |
| `anzsrc_3108` | Plant biology |  |
| `anzsrc_3109` | Zoology |  |
| `anzsrc_3199` | Other biological sciences |  |
| `anzsrc_32` | Biomedical and clinical sciences (all) |  |
| `anzsrc_3201` | Cardiovascular medicine and haematology |  |
| `anzsrc_3202` | Clinical sciences |  |
| `anzsrc_3203` | Dentistry |  |
| `anzsrc_3204` | Immunology |  |
| `anzsrc_3205` | Medical biochemistry and metabolomics |  |
| `anzsrc_3206` | Medical biotechnology |  |
| `anzsrc_3207` | Medical microbiology |  |
| `anzsrc_3208` | Medical physiology |  |
| `anzsrc_3209` | Neurosciences |  |
| `anzsrc_3210` | Nutrition and dietetics |  |
| `anzsrc_3211` | Oncology and carcinogenesis |  |
| `anzsrc_3212` | Ophthalmology and optometry |  |
| `anzsrc_3213` | Paediatrics |  |
| `anzsrc_3214` | Pharmacology and pharmaceutical sciences |  |
| `anzsrc_3215` | Reproductive medicine |  |
| `anzsrc_3299` | Other biomedical and clinical sciences |  |
| `anzsrc_33` | Built environment and design (all) |  |
| `anzsrc_3301` | Architecture |  |
| `anzsrc_3302` | Building |  |
| `anzsrc_3303` | Design |  |
| `anzsrc_3304` | Urban and regional planning |  |
| `anzsrc_3399` | Other built environment and design |  |
| `anzsrc_34` | Chemical sciences (all) | Chemistry |
| `anzsrc_3401` | Analytical chemistry |  |
| `anzsrc_3402` | Inorganic chemistry |  |
| `anzsrc_3403` | Macromolecular and materials chemistry |  |
| `anzsrc_3404` | Medicinal and biomolecular chemistry |  |
| `anzsrc_3405` | Organic chemistry |  |
| `anzsrc_3406` | Physical chemistry |  |
| `anzsrc_3407` | Theoretical and computational chemistry |  |
| `anzsrc_3499` | Other chemical sciences |  |
| `anzsrc_35` | Commerce, management, tourism and services (all) |  |
| `anzsrc_3501` | Accounting, auditing and accountability |  |
| `anzsrc_3502` | Banking, finance and investment |  |
| `anzsrc_3503` | Business systems in context |  |
| `anzsrc_3504` | Commercial services |  |
| `anzsrc_3505` | Human resources and industrial relations |  |
| `anzsrc_3506` | Marketing |  |
| `anzsrc_3507` | Strategy, management and organisational behaviour |  |
| `anzsrc_3508` | Tourism |  |
| `anzsrc_3509` | Transportation, logistics and supply chains |  |
| `anzsrc_3599` | Other commerce, management, tourism and services |  |
| `anzsrc_36` | Creative arts and writing (all) |  |
| `anzsrc_3601` | Art history, theory and criticism |  |
| `anzsrc_3602` | Creative and professional writing |  |
| `anzsrc_3603` | Music |  |
| `anzsrc_3604` | Performing arts |  |
| `anzsrc_3605` | Screen and digital media |  |
| `anzsrc_3606` | Visual arts |  |
| `anzsrc_3699` | Other creative arts and writing |  |
| `anzsrc_37` | Earth sciences (all) | Earth Science, Geology |
| `anzsrc_3701` | Atmospheric sciences |  |
| `anzsrc_3702` | Climate change science | Climate, Earth Science |
| `anzsrc_3703` | Geochemistry |  |
| `anzsrc_3704` | Geoinformatics |  |
| `anzsrc_3705` | Geology |  |
| `anzsrc_3706` | Geophysics |  |
| `anzsrc_3707` | Hydrology |  |
| `anzsrc_3708` | Oceanography |  |
| `anzsrc_3709` | Physical geography and environmental geoscience |  |
| `anzsrc_3799` | Other earth sciences |  |
| `anzsrc_38` | Economics (all) |  |
| `anzsrc_3801` | Applied economics |  |
| `anzsrc_3802` | Econometrics |  |
| `anzsrc_3803` | Economic theory |  |
| `anzsrc_3899` | Other economics |  |
| `anzsrc_39` | Education (all) |  |
| `anzsrc_3901` | Curriculum and pedagogy |  |
| `anzsrc_3902` | Education policy, sociology and philosophy |  |
| `anzsrc_3903` | Education systems |  |
| `anzsrc_3904` | Specialist studies in education |  |
| `anzsrc_3999` | Other Education |  |
| `anzsrc_40` | Engineering (all) | Engineering Education |
| `anzsrc_4001` | Aerospace engineering |  |
| `anzsrc_4002` | Automotive engineering |  |
| `anzsrc_4003` | Biomedical engineering |  |
| `anzsrc_4004` | Chemical engineering |  |
| `anzsrc_4005` | Civil engineering |  |
| `anzsrc_4006` | Communications engineering |  |
| `anzsrc_4007` | Control engineering, mechatronics and robotics |  |
| `anzsrc_4008` | Electrical engineering |  |
| `anzsrc_4009` | Electronics, sensors and digital hardware |  |
| `anzsrc_4010` | Engineering practice and education |  |
| `anzsrc_4011` | Environmental engineering |  |
| `anzsrc_4012` | Fluid mechanics and thermal engineering |  |
| `anzsrc_4013` | Geomatic engineering |  |
| `anzsrc_4014` | Manufacturing engineering |  |
| `anzsrc_4015` | Maritime engineering |  |
| `anzsrc_4016` | Materials engineering |  |
| `anzsrc_4017` | Mechanical engineering |  |
| `anzsrc_4018` | Nanotechnology |  |
| `anzsrc_4019` | Resources engineering and extractive metallurgy |  |
| `anzsrc_4099` | Other engineering |  |
| `anzsrc_41` | Environmental sciences (all) |  |
| `anzsrc_4101` | Climate change impacts and adaptation |  |
| `anzsrc_4102` | Ecological applications |  |
| `anzsrc_4103` | Environmental biotechnology |  |
| `anzsrc_4104` | Environmental management |  |
| `anzsrc_4105` | Pollution and contamination |  |
| `anzsrc_4106` | Soil sciences |  |
| `anzsrc_4199` | Other environmental sciences |  |
| `anzsrc_42` | Health sciences (all) |  |
| `anzsrc_4201` | Allied health and rehabilitation science |  |
| `anzsrc_4202` | Epidemiology |  |
| `anzsrc_4203` | Health services and systems |  |
| `anzsrc_4204` | Midwifery |  |
| `anzsrc_4205` | Nursing |  |
| `anzsrc_4206` | Public health |  |
| `anzsrc_4207` | Sports science and exercise |  |
| `anzsrc_4208` | Traditional, complementary and integrative medicine |  |
| `anzsrc_4299` | Other health sciences |  |
| `anzsrc_43` | History, heritage and archaeology (all) |  |
| `anzsrc_4301` | Archaeology |  |
| `anzsrc_4302` | Heritage, archive and museum studies |  |
| `anzsrc_4303` | Historical studies |  |
| `anzsrc_4399` | Other history, heritage and archaeology |  |
| `anzsrc_44` | Human society (all) |  |
| `anzsrc_4401` | Anthropology |  |
| `anzsrc_4402` | Criminology |  |
| `anzsrc_4403` | Demography |  |
| `anzsrc_4404` | Development studies |  |
| `anzsrc_4405` | Gender studies |  |
| `anzsrc_4406` | Human geography |  |
| `anzsrc_4407` | Policy and administration |  |
| `anzsrc_4408` | Political science |  |
| `anzsrc_4409` | Social work |  |
| `anzsrc_4410` | Sociology |  |
| `anzsrc_4499` | Other human society |  |
| `anzsrc_45` | Indigenous studies (all) |  |
| `anzsrc_4501` | Aboriginal and Torres Strait Islander culture, language and history |  |
| `anzsrc_4502` | Aboriginal and Torres Strait Islander education |  |
| `anzsrc_4503` | Aboriginal and Torres Strait Islander environmental knowledges and management |  |
| `anzsrc_4504` | Aboriginal and Torres Strait Islander health and wellbeing |  |
| `anzsrc_4505` | Aboriginal and Torres Strait Islander peoples, society and community |  |
| `anzsrc_4506` | Aboriginal and Torres Strait Islander sciences |  |
| `anzsrc_4507` | Te ahurea, reo me te hītori o te Māori (Māori culture, language and history) |  |
| `anzsrc_4508` | Mātauranga Māori (Māori education) |  |
| `anzsrc_4509` | Ngā mātauranga taiao o te Māori (Māori environmental knowledges) |  |
| `anzsrc_4510` | Te hauora me te oranga o te Māori (Māori health and wellbeing) |  |
| `anzsrc_4511` | Ngā tāngata, te porihanga me ngā hapori o te Māori (Māori peoples, society and community) |  |
| `anzsrc_4512` | Ngā pūtaiao Māori (Māori sciences) |  |
| `anzsrc_4513` | Pacific Peoples culture, language and history |  |
| `anzsrc_4514` | Pacific Peoples education |  |
| `anzsrc_4515` | Pacific Peoples environmental knowledges |  |
| `anzsrc_4516` | Pacific Peoples health and wellbeing |  |
| `anzsrc_4517` | Pacific Peoples sciences |  |
| `anzsrc_4518` | Pacific Peoples society and community |  |
| `anzsrc_4519` | Other Indigenous data, methodologies and global Indigenous studies |  |
| `anzsrc_4599` | Other Indigenous studies |  |
| `anzsrc_46` | Information and computing sciences (all) | Computer Science Education |
| `anzsrc_4601` | Applied computing |  |
| `anzsrc_4602` | Artificial intelligence |  |
| `anzsrc_4603` | Computer vision and multimedia computation |  |
| `anzsrc_4604` | Cybersecurity and privacy |  |
| `anzsrc_4605` | Data management and data science |  |
| `anzsrc_4606` | Distributed computing and systems software |  |
| `anzsrc_4607` | Graphics, augmented reality and games |  |
| `anzsrc_4608` | Human-centred computing |  |
| `anzsrc_4609` | Information systems |  |
| `anzsrc_4610` | Library and information studies |  |
| `anzsrc_4611` | Machine learning |  |
| `anzsrc_4612` | Software engineering |  |
| `anzsrc_4613` | Theory of computation |  |
| `anzsrc_4699` | Other information and computing sciences |  |
| `anzsrc_47` | Language, communication and culture (all) |  |
| `anzsrc_4701` | Communication and media studies |  |
| `anzsrc_4702` | Cultural studies |  |
| `anzsrc_4703` | Language studies |  |
| `anzsrc_4704` | Linguistics |  |
| `anzsrc_4705` | Literary studies |  |
| `anzsrc_4799` | Other language, communication and culture |  |
| `anzsrc_48` | Law and legal studies (all) |  |
| `anzsrc_4801` | Commercial law |  |
| `anzsrc_4802` | Environmental and resources law |  |
| `anzsrc_4803` | International and comparative law |  |
| `anzsrc_4804` | Law in context |  |
| `anzsrc_4805` | Legal systems |  |
| `anzsrc_4806` | Private law and civil obligations |  |
| `anzsrc_4807` | Public law |  |
| `anzsrc_4899` | Other law and legal studies |  |
| `anzsrc_49` | Mathematical sciences (all) | Mathematics Education |
| `anzsrc_4901` | Applied mathematics |  |
| `anzsrc_4902` | Mathematical physics |  |
| `anzsrc_4903` | Numerical and computational mathematics |  |
| `anzsrc_4904` | Pure mathematics |  |
| `anzsrc_4905` | Statistics |  |
| `anzsrc_4999` | Other mathematical sciences |  |
| `anzsrc_50` | Philosophy and religious studies (all) |  |
| `anzsrc_5001` | Applied ethics |  |
| `anzsrc_5002` | History and philosophy of specific fields |  |
| `anzsrc_5003` | Philosophy |  |
| `anzsrc_5004` | Religious studies |  |
| `anzsrc_5005` | Theology |  |
| `anzsrc_5099` | Other philosophy and religious studies |  |
| `anzsrc_51` | Physical sciences (all) | Physics |
| `anzsrc_5101` | Astronomical sciences | Astronomy |
| `anzsrc_5102` | Atomic, molecular and optical physics |  |
| `anzsrc_5103` | Classical physics |  |
| `anzsrc_5104` | Condensed matter physics |  |
| `anzsrc_5105` | Medical and biological physics |  |
| `anzsrc_5106` | Nuclear and plasma physics |  |
| `anzsrc_5107` | Particle and high energy physics |  |
| `anzsrc_5108` | Quantum physics |  |
| `anzsrc_5109` | Space sciences |  |
| `anzsrc_5110` | Synchrotrons and accelerators |  |
| `anzsrc_5199` | Other physical sciences |  |
| `anzsrc_52` | Psychology (all) |  |
| `anzsrc_5201` | Applied and developmental psychology |  |
| `anzsrc_5202` | Biological psychology |  |
| `anzsrc_5203` | Clinical and health psychology |  |
| `anzsrc_5204` | Cognitive and computational psychology |  |
| `anzsrc_5205` | Social and personality psychology |  |
| `anzsrc_5299` | Other psychology |  |
| `discipline_general` | Not specific to a discipline |  |
| `biology` | Biology and life sciences | Biology |
| `chemistry` | Chemistry | Chemistry |
| `physics` | Physics | Physics |
| `geoscience` | Geoscience / Earth science | Earth Science, Geology |
| `climate_science` | Climate and environmental science | Climate, Earth Science |
| `astronomy` | Astronomy and space science | Astronomy |
| `mathematics` | Mathematics and statistics | Mathematics Education |
| `computer_science` | Computer science and computing | Computer Science Education |
| `engineering` | Engineering | Engineering Education |
| `general_stem` | General or interdisciplinary STEM | Science Education, STEM Education |
| `psychology` | Psychology |  |
| `economics` | Economics and business |  |
| `education_studies` | Education (as a subject: policy, foundations, teaching and learning) |  |
| `sociology` | Sociology and demography |  |
| `anthropology` | Anthropology and ethnology |  |
| `law` | Law |  |
| `political_science` | Political science and public policy |  |
| `human_geography` | Social and economic geography |  |
| `media_communication` | Media and communication |  |
| `history` | History |  |
| `archaeology` | Archaeology |  |
| `languages_literature` | Languages, literature, and linguistics |  |
| `philosophy_religion` | Philosophy, ethics, and religion |  |
| `visual_arts` | Visual arts, design, and art history |  |
| `performing_arts` | Performing arts and music |  |
| `other_humanities` | Other humanities (e.g., cultural studies, digital humanities) |  |
| `other_social_science` | Other social sciences |  |
| `other_discipline` | Other discipline |  |

### <a id="human_participants"></a>Human participants (`human_participants`)

Whether people take part in the study. Decides which population and consent fields apply.

| Code | Label | ERIC descriptors |
|---|---|---|
| `direct` | Yes: people take part directly (surveys, interviews, observation, tests, creative work) |  |
| `indirect` | Indirectly: data are about people who do not take part (records, public online posts) |  |
| `none` | No: the study uses only texts, artworks, objects, or other non-human sources |  |

### <a id="participant_role"></a>Participant population (`participant_role`)

Who the participants are.

| Code | Label | ERIC descriptors |
|---|---|---|
| `students` | Students / learners |  |
| `educators` | Teachers, instructors, or teaching assistants | Teachers, College Faculty, Teaching Assistants |
| `professionals` | Researchers or other professionals |  |
| `children_youth` | Children or youth |  |
| `adults` | Adults | Adults |
| `families` | Families or household groups |  |
| `visitors` | Museum, science-center, or event visitors | Museums |
| `community_members` | Community members / general public |  |
| `specific_community` | A specific community or cultural group |  |
| `artists_creators` | Artists, writers, performers, or other creators |  |
| `online_authors` | Authors of online content (e.g., social media users) |  |
| `staff_leaders` | Staff, administrators, or organizational leaders |  |
| `other_participants` | Other participants |  |

### <a id="education_level"></a>Education level (`education_level`)

Education level(s) of the participants. Levels 0–8 are the UNESCO ISCED 2011 levels of education; the last two options are HuMeta additions outside ISCED.

| Code | Label | ERIC descriptors |
|---|---|---|
| `early_childhood` | Early childhood / pre-K (ISCED 0) | Early Childhood Education |
| `primary` | Primary / elementary (ISCED 1) | Elementary Education |
| `lower_secondary` | Lower secondary / middle grades (ISCED 2) | Middle Schools, Secondary Education |
| `upper_secondary` | Upper secondary / high school (ISCED 3) | High Schools, Secondary Education |
| `postsecondary_non_tertiary` | Post-secondary non-tertiary, e.g. certificate programs (ISCED 4) | Postsecondary Education |
| `short_cycle_tertiary` | Short-cycle tertiary, e.g. associate degree (ISCED 5) | Two Year Colleges, Postsecondary Education |
| `bachelors` | Bachelor's or equivalent (ISCED 6) | Higher Education, Postsecondary Education, Undergraduate Students |
| `masters` | Master's or equivalent (ISCED 7) | Higher Education, Graduate Students |
| `doctoral` | Doctoral or equivalent (ISCED 8) | Higher Education, Graduate Students |
| `adult_education` | Adult, continuing, or workforce education (not an ISCED level) | Adult Education, Adults |
| `informal_learning` | Informal or out-of-school learning (not an ISCED level) | Informal Education |

### <a id="undergraduate_level"></a>Undergraduate course level (`undergraduate_level`)

For undergraduate studies, the course level(s) involved.

| Code | Label | ERIC descriptors |
|---|---|---|
| `introductory` | Introductory / first-year |  |
| `intermediate` | Intermediate / second-year |  |
| `advanced` | Advanced / third- or fourth-year |  |
| `capstone` | Upper-division / capstone |  |

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
| `online_synchronous` | Online, synchronous | Online Courses, Synchronous Communication |
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
| `out_of_school_program` | Afterschool, summer, or out-of-school program | After School Programs, Summer Programs |
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
| `student_centered` | Student-centered | Student Centered Learning |
| `research_experience` | Course-based or apprenticed research experience | Undergraduate Study |
| `other_pedagogy` | Other |  |

### <a id="study_design"></a>Study design (evidence type) (`study_design`)

The design that produced the evidence in the resource.

| Code | Label | ERIC descriptors |
|---|---|---|
| `cross_sectional` | Cross-sectional (single time point) |  |
| `descriptive` | Descriptive | Educational Research |
| `correlational` | Correlational | Correlation |
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
| `ethnographic` | Ethnographic study | Ethnography |
| `historical` | Historical study |  |
| `interpretive_critical` | Interpretive, critical, or theoretical study |  |
| `practice_based` | Practice-based or creative research (e.g., making artworks, performances, designs) |  |

### <a id="unit_of_analysis"></a>Unit of analysis (`unit_of_analysis`)

The unit the analysis is about. Follows the DDI AnalysisUnit vocabulary (2.1.3).

| Code | Label | ERIC descriptors |
|---|---|---|
| `individual` | Individual (person) |  |
| `group` | Group (e.g., class, team, community) |  |
| `family_household` | Family or household |  |
| `organization` | Organization or institution |  |
| `event` | Event, process, or activity |  |
| `place` | Geographic or political-administrative area |  |
| `time_unit` | Time unit (e.g., year, period) |  |
| `text` | Text (e.g., document, book, post, transcript) |  |
| `still_image` | Still image (e.g., photograph, artwork) |  |
| `sound` | Sound (e.g., music, audio recording) |  |
| `video` | Video or film |  |
| `object` | Object or artifact |  |
| `other_unit` | Other or multi-level |  |

### <a id="sampling_procedure"></a>Sampling procedure (`sampling_procedure`)

How cases (people, texts, objects, sites) were selected. Follows the DDI SamplingProcedure vocabulary (2.0.2).

| Code | Label | ERIC descriptors |
|---|---|---|
| `census` | Total universe / complete enumeration (all eligible cases) |  |
| `simple_random` | Probability: simple random |  |
| `systematic` | Probability: systematic random (e.g., every nth on a list) |  |
| `stratified` | Probability: stratified |  |
| `cluster` | Probability: cluster (e.g., whole classes or schools) |  |
| `multistage` | Probability: multistage |  |
| `convenience` | Non-probability: availability / convenience (including volunteers) |  |
| `purposive` | Non-probability: purposive / criterion-based |  |
| `quota` | Non-probability: quota |  |
| `snowball` | Non-probability: respondent-assisted / snowball |  |
| `theoretical` | Theoretical sampling (cases chosen as theory develops) |  |
| `mixed_sampling` | Mixed probability and non-probability |  |
| `other_sampling` | Other |  |

### <a id="measurement_evidence"></a>Measurement evidence (`measurement_evidence`)

Kinds of reliability or validity evidence the resource provides, following the sources of validity evidence in the Standards for Educational and Psychological Testing (AERA, APA, NCME, 2014).

| Code | Label | ERIC descriptors |
|---|---|---|
| `test_content` | Evidence based on test content | Content Validity, Test Validity |
| `response_processes` | Evidence based on response processes | Test Validity |
| `internal_structure` | Evidence based on internal structure | Construct Validity, Factor Analysis |
| `relations_to_other_variables` | Evidence based on relations to other variables | Predictive Validity, Test Validity |
| `consequences` | Evidence based on consequences of testing | Test Validity |
| `reliability` | Reliability / precision | Test Reliability |
| `fairness` | Fairness / differential item functioning | Test Bias |
| `irt_scaling` | Item response theory scaling | Item Response Theory |

### <a id="data_collection_method"></a>Data collection method (`data_collection_method`)

How data or sources were gathered. Each term maps to the DDI ModeOfCollection vocabulary (5.0.1).

| Code | Label | ERIC descriptors |
|---|---|---|
| `survey` | Survey or questionnaire | Questionnaires, Surveys |
| `assessment` | Test or assessment | Tests |
| `experiment` | Experiment (laboratory, field, or web-based) |  |
| `interview` | Interview | Interviews |
| `focus_group` | Focus group | Focus Groups |
| `observation` | Observation (non-participant) | Observation, Classroom Observation Techniques |
| `ethnography` | Ethnography / participant observation | Ethnography, Participant Observation |
| `diaries` | Diaries, journals, or reflective writing |  |
| `recording` | Audio or video recording |  |
| `visual_methods` | Visual or arts-based methods (e.g., photo elicitation, photovoice, drawing) |  |
| `artifacts` | Work samples, documents, or artifacts produced by participants (e.g., student work) | Content Analysis |
| `archival_research` | Archival research (finding and selecting records in archives or collections) |  |
| `corpus_collection` | Assembling a corpus of texts, images, or media (e.g., published works, news) |  |
| `web_platform_data` | Web or platform data collection (API, scraping, data donation) |  |
| `learning_analytics` | Learning analytics or system log data | Learning Analytics |
| `institutional_records` | Institutional or administrative records | Student Records |
| `practice_based` | Practice-based or creative making (artworks, performances, designs) |  |
| `other_method` | Other |  |

### <a id="analysis_method"></a>Analysis method (`analysis_method`)

How the data or sources were analyzed. Covers quantitative, qualitative, interpretive, and computational approaches.

| Code | Label | ERIC descriptors |
|---|---|---|
| `statistical` | Statistical or quantitative analysis | Data Analysis |
| `psychometric` | Psychometric or measurement modeling (e.g., factor analysis, IRT) | Psychometrics |
| `thematic` | Qualitative coding or thematic analysis | Qualitative Research |
| `content_analysis` | Content analysis | Content Analysis |
| `discourse_analysis` | Discourse or conversation analysis |  |
| `close_reading` | Close reading or textual analysis |  |
| `visual_analysis` | Visual or image analysis (e.g., photographs, artworks, film) |  |
| `historical_analysis` | Historical analysis or source criticism |  |
| `ethnographic_analysis` | Ethnographic or interpretive analysis |  |
| `critical_theoretical` | Critical or theoretical analysis |  |
| `computational` | Computational text or media analysis (e.g., text mining, NLP, image recognition) |  |
| `network_analysis` | Network analysis |  |
| `spatial_analysis` | Spatial or geographic analysis |  |
| `case_analysis` | Case analysis or comparative case study | Case Studies |
| `other_analysis` | Other |  |

### <a id="source_type"></a>Source type (`source_type`)

Kinds of sources studied that are not (only) data collected from participants: texts, images, artworks, media, records, objects, and online content. Mapped to DDI GeneralDataFormat and DataSourceType.

| Code | Label | ERIC descriptors |
|---|---|---|
| `texts` | Texts and documents (books, manuscripts, letters, policies, curricula) |  |
| `archival_records` | Archival or historical records |  |
| `administrative_records` | Administrative or institutional records |  |
| `photographs` | Photographs and other images |  |
| `artworks` | Artworks (including participant or student artwork) |  |
| `audio` | Audio and music recordings |  |
| `video_film` | Video and film |  |
| `news_media` | News and broadcast media |  |
| `social_media` | Social media and online platform content |  |
| `websites` | Websites and web archives |  |
| `correspondence` | Private correspondence and personal papers |  |
| `objects` | Material objects and artifacts |  |
| `performances` | Performances and events |  |
| `maps_geospatial` | Maps and geospatial data |  |
| `existing_datasets` | Existing research datasets |  |
| `software_games` | Software, games, or digital tools |  |
| `other_source` | Other |  |

### <a id="source_rights"></a>Rights status of sources (`source_rights`)

Copyright or other rights status of the sources studied. Decides whether copies of sources can be shared. Related to RightsStatements.org statements.

| Code | Label | ERIC descriptors |
|---|---|---|
| `public_domain` | Public domain or no known copyright |  |
| `open_license` | Openly licensed (e.g., Creative Commons) |  |
| `permission` | In copyright, used with permission from rights holders |  |
| `in_copyright` | In copyright, used under an exception such as fair use (copies not shared) |  |
| `platform_terms` | Governed by platform terms of service |  |
| `mixed_rights` | Mixed: sources have different rights |  |
| `unknown_rights` | Not yet evaluated |  |

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
| `education_records` | Education records (FERPA) | Student Records, Privacy |
| `public_online_content` | Public online content that can be traced to its authors |  |

### <a id="online_data_practice"></a>Online data practices (`online_data_practice`)

How content collected from websites, social media, or other online platforms was handled. Informed by the Association of Internet Researchers' Internet Research: Ethical Guidelines 3.0 (2019).

| Code | Label | ERIC descriptors |
|---|---|---|
| `public_content` | Content was publicly available (no login or membership needed) |  |
| `private_spaces` | Some content is from closed or semi-private spaces (groups, forums, chats needing login) |  |
| `platform_terms` | Collected under the platform's terms of service or a data-access agreement |  |
| `author_consent` | Authors gave consent |  |
| `no_consent_public` | Consent not sought (public content; ethics review agreed or determined not needed) |  |
| `usernames_removed` | Usernames and profile details removed or replaced |  |
| `quotes_altered` | Quotes paraphrased or altered so authors cannot be found by searching |  |
| `ids_only` | Only post IDs or derived data are shared, not the content itself |  |
| `deletions_honored` | Content later deleted by its authors is removed from the dataset |  |
| `minors_possible` | Authors may include minors |  |

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

### <a id="kind_of_data"></a>Kind of data (`kind_of_data`)

Whether the data are quantitative, qualitative, or both. DDI Alliance KindOfData controlled vocabulary 1.0.0. Quantitative: numbers that can be counted, measured, and analyzed statistically. Qualitative: non-numeric data such as texts, images, or recordings, analyzed interpretively. Mixed: both.

| Code | Label | ERIC descriptors |
|---|---|---|
| `quantitative` | Quantitative |  |
| `qualitative` | Qualitative |  |
| `mixed` | Mixed (quantitative and qualitative) |  |

### <a id="tadirah_activity"></a>Research activity (TaDiRAH) (`tadirah_activity`)

Research activities from TaDiRAH 2.0.3, the Taxonomy of Digital Research Activities in the Humanities (DARIAH; CC0). Each term is a second-level TaDiRAH concept, shown with its top-level activity; 'tadirah' is the concept's identifier at https://vocabs.dariah.eu/tadirah/.

| Code | Label | ERIC descriptors |
|---|---|---|
| `converting` | Capturing: Converting |  |
| `data_recognition` | Capturing: Data Recognition |  |
| `discovering` | Capturing: Discovering |  |
| `extracting` | Capturing: Extracting |  |
| `gathering` | Capturing: Gathering |  |
| `imaging` | Capturing: Imaging |  |
| `recording` | Capturing: Recording |  |
| `transcribing` | Capturing: Transcribing |  |
| `annotating` | Enriching: Annotating |  |
| `data_cleansing` | Enriching: Data Cleansing |  |
| `editing` | Enriching: Editing |  |
| `content_analysis` | Analyzing: Content Analysis |  |
| `network_analysis` | Analyzing: Network Analysis |  |
| `relational_analysis` | Analyzing: Relational Analysis |  |
| `spatial_analysis` | Analyzing: Spatial Analysis |  |
| `structural_analysis` | Analyzing: Structural Analysis |  |
| `stylistic_analysis` | Analyzing: Stylistic Analysis |  |
| `visual_analysis` | Analyzing: Visual Analysis |  |
| `contextualizing` | Interpreting: Contextualizing |  |
| `modeling` | Interpreting: Modeling |  |
| `theorizing` | Interpreting: Theorizing |  |
| `archiving` | Storing: Archiving |  |
| `identifying` | Storing: Identifying |  |
| `organizing` | Storing: Organizing |  |
| `preserving` | Storing: Preserving |  |
| `designing` | Creating: Designing |  |
| `programming` | Creating: Programming |  |
| `translating` | Creating: Translating |  |
| `web_development` | Creating: Web Development |  |
| `writing` | Creating: Writing |  |
| `collaborating` | Disseminating: Collaborating |  |
| `commenting` | Disseminating: Commenting |  |
| `communicating` | Disseminating: Communicating |  |
| `crowdsourcing` | Disseminating: Crowdsourcing |  |
| `publishing` | Disseminating: Publishing |  |
| `teaching` | Disseminating: Teaching |  |

### <a id="constructs"></a>Constructs

Defined in [`library/constructs.json`](https://github.com/JLib271/HuMeta/blob/main/library/constructs.json).

| Code | Label | Definition | ERIC descriptors |
|---|---|---|---|
| `conceptual_understanding` | Conceptual understanding | Grasp of core disciplinary ideas and the ability to apply them to new situations, as distinct from recall or procedural skill. | Scientific Concepts, Misconceptions, Concept Formation |
| `climate_change_conceptual_understanding` | Climate change conceptual understanding | Understanding of the scientific ideas behind climate and climate change, such as Earth's energy balance, the greenhouse effect, the carbon cycle, and natural and human causes of change, including common alternative conceptions. | Climate, Scientific Concepts |
| `content_knowledge` | Content knowledge | Factual and procedural knowledge of a subject area, as typically measured by course exams or knowledge tests. | Knowledge Level, Academic Achievement |
| `problem_solving` | Problem solving | Approaches and skill in working through unfamiliar disciplinary problems, including planning, representation and checking. | Problem Solving |
| `scientific_reasoning` | Scientific reasoning | Reasoning about evidence, variables, models and experiments, including control of variables and proportional reasoning. | Science Process Skills, Scientific Literacy |
| `quantitative_reasoning` | Quantitative reasoning | Using numbers, graphs and mathematical relationships to make sense of disciplinary situations. | Numeracy, Mathematical Logic |
| `self_efficacy` | Self-efficacy | A person's belief in their capability to succeed at specific tasks or in a specific domain. | Self Efficacy |
| `perceived_behavioral_control` | Perceived behavioral control | Perceived ease or difficulty of performing a behavior, including access to needed resources (Theory of Planned Behavior). | Locus of Control |
| `interest` | Interest | Enjoyment of and desire to engage with a subject, either in the moment (situational) or as an enduring disposition (individual). | Student Interests |
| `task_value` | Task value | How interesting, important and useful a person judges a subject or task to be, and what it costs them to engage. | Values, Expectation |
| `goal_orientation` | Goal orientation | The reasons a learner pursues academic tasks, such as mastering material versus demonstrating ability or earning grades. | Goal Orientation |
| `anxiety` | Academic anxiety | Worry and emotional arousal related to a subject or to evaluation within it. | Anxiety, Test Anxiety, Mathematics Anxiety |
| `attitude_toward_subject` | Attitude toward the subject or behavior | Overall positive or negative evaluation of a subject, activity or behavior. | Scientific Attitudes, Student Attitudes |
| `behavioral_intention` | Behavioral intention | Stated readiness or plan to perform a behavior, such as taking further courses or pursuing a major or career. | Intention, Academic Persistence |
| `mindset` | Mindset / beliefs about ability | Beliefs about whether ability in a domain is fixed or can be developed, and about who can succeed. | Beliefs, Self Concept |
| `sense_of_belonging` | Sense of belonging | Feeling accepted, valued and included as a member of a course, discipline, institution or community. | Sense of Belonging |
| `disciplinary_identity` | Disciplinary identity | Seeing oneself, and being recognized by others, as the kind of person who does a discipline (e.g. a physics person, a scientist). | Professional Identity, Identification (Psychology) |
| `subjective_norm` | Subjective norm | Perceived expectations from important others about whether one should perform a behavior. | Social Influences, Peer Influence |
| `stereotype_perception` | Perceived stereotypes and climate | Awareness of stereotypes about who belongs or succeeds in a field, and perception of bias in the learning environment. | Stereotypes, Educational Environment |
| `community_connectedness` | Classroom community | Perceived cohesion, trust and mutual support among learners and instructors in a learning setting. | Sense of Community |
| `epistemological_beliefs` | Beliefs about the discipline and learning it | Beliefs about the nature of disciplinary knowledge and about what learning the discipline involves, often compared with expert views. | Epistemology, Beliefs |
| `nature_of_science` | Understanding of the nature of science | Understanding of how scientific knowledge is generated, justified and revised. | Scientific Literacy, Epistemology |
| `real_world_relevance` | Perceived real-world relevance | Seeing connections between disciplinary content and everyday life or societal issues. | Relevance (Education) |
| `self_regulated_learning` | Self-regulated learning | Planning, monitoring and adjusting one's own learning, including metacognition and management of time and effort. | Metacognition, Self Management |
| `learning_strategies` | Study and learning strategies | Specific cognitive and resource-management strategies used when studying, such as rehearsal, elaboration, organization and help seeking. | Learning Strategies, Study Habits |
| `engagement` | Engagement | Behavioral, cognitive and emotional involvement in learning activities. | Learner Engagement |
| `critical_thinking` | Critical thinking | Evaluating claims, evidence and arguments and applying prior knowledge to new problems. | Critical Thinking |
| `teaching_practices` | Teaching practices | What instructors do during instruction, such as lecturing, posing questions, facilitating group work or giving feedback. | Teaching Methods |
| `student_classroom_activity` | Student classroom activity | What students are observed doing during instruction, such as listening, discussing, working in groups or answering questions. | Classroom Observation Techniques, Student Behavior |
| `reformed_teaching` | Reformed / student-centered teaching | Degree to which instruction is inquiry-oriented and student-centered rather than transmission-oriented. | Active Learning, Inquiry, Student Centered Learning |
| `teaching_beliefs` | Instructor beliefs about teaching | Instructors' beliefs about how students learn and what effective teaching looks like. | Teacher Attitudes, Beliefs |
| `learning_environment` | Learning environment perceptions | Learners' perceptions of course structure, support, fairness and climate. | Classroom Environment, Educational Environment |
