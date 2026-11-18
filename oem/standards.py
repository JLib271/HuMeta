"""The standards, vocabularies and practices HuMeta builds on, credited in one place.

Shown on the HuMeta Portal's About page and on the HuMeta Instrument Library website's About page.
The profile's own standards (its ``standards`` block, which element alignments point to) are read from
the profile, so the list stays in step with it; what the Portal and the Library use beyond the profile
is listed here. Each entry says where HuMeta uses it.
"""
from __future__ import annotations

from oem import profile as P

#: Groups, in display order
GROUPS = (
    "Metadata schemas and formats",
    "Vocabularies and classifications",
    "Identifiers and registries",
    "Ethics, rights and Indigenous data governance",
    "Measurement and data practice",
    "Compared with",
)

#: Where HuMeta uses each standard in the profile's ``standards`` block: (group, use)
PROFILE_USES = {
    "datacite": ("Metadata schemas and formats",
                 "Study and dataset records export to DataCite 4.7 for DOIs; instruments are linked with IsCollectedBy."),
    "dcterms": ("Metadata schemas and formats", "Element alignments, so records map to Dublin Core."),
    "schemaorg": ("Metadata schemas and formats", "Dataset and instrument pages carry schema.org descriptions for search engines."),
    "ddi": ("Metadata schemas and formats", "Codebooks export as DDI-Codebook 2.5, with variables, concepts and metadata codes."),
    "tei": ("Metadata schemas and formats", "Named for humanities studies that encode texts."),
    "iso8601": ("Metadata schemas and formats", "All dates."),
    "ddi_cv": ("Vocabularies and classifications",
               "Unit of analysis, sampling procedure, mode of collection, time method, data format, source type and kind of data map to DDI terms."),
    "eric": ("Vocabularies and classifications", "Construct names (first choice), discipline descriptors and DataCite subjects."),
    "anzsrc": ("Vocabularies and classifications", "The discipline vocabulary (divisions and groups), CC BY 4.0."),
    "fos": ("Vocabularies and classifications", "Each discipline's OECD field, for DataCite subjects."),
    "isced": ("Vocabularies and classifications", "Education levels (ISCED 2011 levels 0 to 8)."),
    "nces_locale": ("Vocabularies and classifications", "US school and college locale (city, suburb, town, rural)."),
    "tadirah": ("Vocabularies and classifications", "Research activities for humanities studies, CC0."),
    "spdx": ("Vocabularies and classifications", "Data and instrument licenses."),
    "bcp47": ("Vocabularies and classifications", "Language tags."),
    "iso639": ("Vocabularies and classifications", "Language codes inside language tags."),
    "iso3166": ("Vocabularies and classifications", "Country codes."),
    "orcid": ("Identifiers and registries", "Researchers and instrument developers."),
    "rightsstatements": ("Ethics, rights and Indigenous data governance", "Rights status of sources such as archival materials."),
    "common_rule": ("Ethics, rights and Indigenous data governance", "US human-subjects review and consent fields."),
    "ferpa": ("Ethics, rights and Indigenous data governance", "US student-records privacy in the responsible-sharing rules."),
    "care": ("Ethics, rights and Indigenous data governance", "Indigenous data fields and governance rules."),
    "local_contexts": ("Ethics, rights and Indigenous data governance", "Traditional Knowledge and Biocultural Labels and Notices."),
    "aoir": ("Ethics, rights and Indigenous data governance", "Online data practices for studies of online material."),
    "testing_standards": ("Measurement and data practice",
                          "The five sources of validity evidence used for measurement evidence and instrument records."),
}

#: Used by the Portal and the Instrument Library beyond the profile: (name, url, group, use)
EXTRA = (
    ("ICPSR Subject Thesaurus", "https://www.icpsr.umich.edu/web/ICPSR/thesaurus/10001",
     "Vocabularies and classifications", "Construct names when ERIC has no exact term."),
    ("ICPSR variable metadata", "https://www.icpsr.umich.edu/web/ICPSR/search/variables",
     "Vocabularies and classifications", "Linked standard variables, and other variables researchers add from ICPSR."),
    ("US OMB Statistical Policy Directive No. 15 (2024)",
     "https://www.federalregister.gov/documents/2024/03/29/2024-06469/revisions-to-ombs-statistical-policy-directive-no-15-standards-for-maintaining-collecting-and",
     "Vocabularies and classifications", "The race and ethnicity standard variable."),
    ("US NCES Classification of Instructional Programs (CIP)", "https://nces.ed.gov/ipeds/cipcode/",
     "Vocabularies and classifications", "The major (field of study) standard variable."),
    ("w3id.org permanent identifiers", "https://w3id.org/",
     "Identifiers and registries", "Persistent identifiers for library instruments, versions, items, constructs and frameworks."),
    ("McMurry et al. (2017), Identifiers for the 21st century", "https://doi.org/10.1371/journal.pbio.2001414",
     "Identifiers and registries", "The ten lessons behind HuMeta's identifier policy."),
    ("APA PsycTests", "https://www.apa.org/pubs/databases/psyctests",
     "Identifiers and registries", "First-choice registry for instrument DOIs."),
    ("ZIS (GESIS), Open Test Archive (ZPID), FDZ Bildung (DIPF)", "https://zis.gesis.org/",
     "Identifiers and registries", "Registries whose instrument DOIs the library links to."),
    ("LOINC", "https://loinc.org/", "Identifiers and registries", "Codes for health survey instruments."),
    ("PhysPort, CHIRAL and edinstruments.org", "https://www.physport.org/",
     "Identifiers and registries", "Instrument catalogs the library links to."),
    ("FAIR Guiding Principles (Wilkinson et al. 2016)", "https://doi.org/10.1038/sdata.2016.18",
     "Measurement and data practice", "The FAIR table on the About page."),
    ("Citation File Format", "https://citation-file-format.github.io/",
     "Measurement and data practice", "How the library and the Portal say how to cite them."),
    ("Software Heritage", "https://www.softwareheritage.org/",
     "Measurement and data practice", "Archives the library's source with each release."),
    ("NEON (National Ecological Observatory Network)", "https://www.neonscience.org/",
     "Compared with", "Ecology's observatory data practice, used as a point of comparison for how data are packaged, "
     "versioned, flagged and combined."),
)


def entries(profile: P.Profile | None = None) -> list[dict]:
    """Every standard HuMeta credits: name, url, group, use. Profile standards first, then the rest."""
    p = profile or P.load()
    out = []
    for key, std in p.definition["standards"].items():
        if key == "humeta":
            continue
        group, use = PROFILE_USES.get(key, ("Metadata schemas and formats", "Element alignments."))
        out.append({"key": key, "name": std["name"], "url": std["url"], "group": group, "use": use})
    out += [{"key": None, "name": n, "url": u, "group": g, "use": use} for n, u, g, use in EXTRA]
    return out


def grouped(profile: P.Profile | None = None) -> list[tuple[str, list[dict]]]:
    """(group, entries) in display order."""
    items = entries(profile)
    return [(g, [e for e in items if e["group"] == g]) for g in GROUPS if any(e["group"] == g for e in items)]


def markdown(profile: P.Profile | None = None) -> str:
    """The list as Markdown: one table per group."""
    parts = []
    for group, items in grouped(profile):
        rows = "\n".join(f"| [{e['name']}]({e['url']}) | {e['use']} |" for e in items)
        parts.append(f"**{group}**\n\n| Standard | How HuMeta uses it |\n| --- | --- |\n{rows}")
    return "\n\n".join(parts)
