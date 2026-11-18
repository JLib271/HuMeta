# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""How HuMeta follows the FAIR Guiding Principles (Wilkinson et al., 2016), one row per principle.

Shown on the portal's About page. Keep the status honest: "Partly" where HuMeta does not yet fully
meet a principle, and say what is missing.
"""

from __future__ import annotations

SOURCE = "Wilkinson et al. (2016), The FAIR Guiding Principles for scientific data management and stewardship"
SOURCE_URL = "https://doi.org/10.1038/sdata.2016.18"
STATUSES = ("Met", "Partly")

#: (principle, what it asks, how HuMeta meets it, status)
PRINCIPLES: list[tuple[str, str, str, str]] = [
    ("F1", "Metadata and data have a globally unique, persistent identifier",
     "Each study gets its own DOI when registered in the STEMEd+ Commons Library (Module 3), and each dataset gets "
     "one when deposited (Module 4). Every library instrument, instrument version, item, construct, and theory has "
     "a persistent identifier (https://w3id.org/humeta/…). A published instrument that is not in the library is "
     "identified by its DOI.", "Met"),
    ("F2", "Data are described with rich metadata",
     "The HuMeta study profile records the study's design, population, setting, theory, constructs, measures, "
     "ethics, and Indigenous data governance (CARE). The codebook describes every variable, down to the item, and "
     "is exported as DDI-Codebook.", "Met"),
    ("F3", "Metadata include the identifier of the data they describe",
     "The study profile (humeta.json) carries the study's DOI; datasets list the study DOI as a related work; every "
     "codebook variable names the persistent identifiers of its construct, measure, and item.", "Met"),
    ("F4", "Metadata are registered or indexed in a searchable resource",
     "Study and dataset DOIs are registered with DataCite through the STEMEd+ Commons Library, with HuMeta keywords "
     "that link them to instruments, constructs, and theories. The HuMeta Library website lists studies, datasets, "
     "and instruments, and describes them for search engines (schema.org). Library instruments are not yet in "
     "DataCite: that needs a DOI for each, deposited by its developers.", "Partly"),
    ("A1", "Metadata are retrievable by their identifier using a standard protocol",
     "DOIs and w3id identifiers resolve over HTTPS to pages and to machine-readable records (JSON).", "Met"),
    ("A1.1", "The protocol is open, free, and universally implementable",
     "HTTPS; no software or account is needed to read any metadata.", "Met"),
    ("A1.2", "The protocol allows authentication and authorization where needed",
     "Data files can be restricted in the STEMEd+ Commons Library, which requires sign-in to request them, while "
     "their metadata stay public. The portal itself never receives research data.", "Met"),
    ("A2", "Metadata stay accessible even when the data are no longer available",
     "DOI metadata are kept by DataCite even if files are withdrawn, and restricted datasets keep public metadata. "
     "The instrument library is kept on GitHub and its website; an archived copy with a DOI for each library "
     "release is still to come.", "Partly"),
    ("I1", "Metadata use a formal, accessible, shared language",
     "JSON with published JSON Schemas, DataCite 4.7 (JSON and XML), DDI-Codebook 2.5, schema.org JSON-LD, and "
     "Dublin Core alignments.", "Met"),
    ("I2", "Metadata use vocabularies that follow FAIR principles",
     "Profile vocabularies are mapped to the ERIC Thesaurus, the ICPSR Subject Thesaurus, ANZSRC and OECD Fields of "
     "Science, ISCED, US NCES, and DDI controlled vocabularies. HuMeta's shared constructs and theories have "
     "persistent identifiers. The names of 32 shared constructs are still awaiting governance review.", "Partly"),
    ("I3", "Metadata include qualified references to other metadata",
     "Links are typed with DataCite relation types (References, IsCollectedBy, IsDescribedBy, …): studies to "
     "instruments and papers, datasets to their study. Item links across instrument versions say how the items "
     "differ and whether the link is possible or confirmed.", "Met"),
    ("R1", "Metadata have a plurality of accurate and relevant attributes",
     "The profile's rules check that a record is consistent (consent, de-identification, review status, CARE) "
     "before it is shared; instruments carry their reliability and validity evidence.", "Met"),
    ("R1.1", "Metadata and data have a clear and accessible usage license",
     "Researchers choose a license for their data (Module 4). Library records are CC BY-SA 4.0, and each "
     "instrument's terms of use are recorded.", "Met"),
    ("R1.2", "Metadata are associated with detailed provenance",
     "Each study records its design, theory, and review status; construct names record their source; evidence "
     "records cite where each result comes from; item links record their basis, who checked them, and when.", "Met"),
    ("R1.3", "Metadata meet domain-relevant community standards",
     "DataCite, DDI, the ERIC Thesaurus, ICPSR variables, and the CARE Principles (Local Contexts). The HuMeta "
     "metadata code (Construct_Measure_Item_Target) is HuMeta's own convention, published with a persistent "
     "identifier (https://w3id.org/humeta/metadata-code); it is not yet a community standard.", "Partly"),
]


def markdown_table() -> str:
    """The principles as a Markdown table."""
    rows = ["| Principle | What it asks | How HuMeta meets it | Status |", "|---|---|---|---|"]
    for pid, asks, how, status in PRINCIPLES:
        rows.append(f"| **{pid}** | {asks} | {how} | {'✅' if status == 'Met' else '◐'} {status} |")
    return "\n".join(rows)
