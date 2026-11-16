# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Datasets in the STEMEd+ Library, and how a study connects to them.

Research data are deposited in the STEMEd+ Library's Data collection on
Knowledge Commons, not in the portal. The HuMeta Library website reads that
collection daily and publishes an index, ``data/datasets.json``, linking each
deposit to the instruments, constructs, and theories it used (built by
humeta-library's ``scripts/fetch_datasets.py``). This module:

* turns a study profile into the **HuMeta keywords** depositors add to their
  deposit (``humeta:instrument:<id>`` and so on), which is how deposits are
  linked even when their files are restricted; and
* reads the index and finds the datasets **related** to a study.

Nothing here imports Streamlit.
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field

from oem.vocab import LIBRARY_SITE_URL

#: The STEMEd+ Library's Data subcollection on Knowledge Commons (KCWorks)
DATA_COLLECTION = "stemedplus-data"
DATA_COLLECTION_URL = f"https://works.hcommons.org/collections/{DATA_COLLECTION}"
DATA_DEPOSIT_URL = f"https://works.hcommons.org/uploads/new?community={DATA_COLLECTION}"
#: The STEMEd+ Library's Studies subcollection, where researchers register a study (its design) for a DOI
STUDIES_COLLECTION = "stemedplus-studies"
STUDIES_COLLECTION_URL = f"https://works.hcommons.org/collections/{STUDIES_COLLECTION}"
STUDIES_DEPOSIT_URL = f"https://works.hcommons.org/uploads/new?community={STUDIES_COLLECTION}"
#: Publisher of every Knowledge Commons Works DOI, used when a registered study has none recorded
KC_PUBLISHER = "Knowledge Commons"
#: The index the HuMeta Library website publishes
DATASET_INDEX_URL = LIBRARY_SITE_URL + "data/datasets.json"
DATASETS_PAGE_URL = LIBRARY_SITE_URL + "datasets/"

#: How much each kind of shared link counts when ranking related datasets
WEIGHTS = {"instruments": 3, "constructs": 2, "frameworks": 2, "disciplines": 1, "education_levels": 1}
REASONS = {"instruments": "instrument", "constructs": "construct", "frameworks": "theory",
           "disciplines": "discipline", "education_levels": "education level"}


def study_links(record: dict | None) -> dict[str, list[str]]:
    """What a HuMeta study profile connects to: instruments, versions, constructs, theories, disciplines, levels."""
    record = record or {}
    study = record.get("study") or {}
    constructs = study.get("constructs") or []

    def unique(values):
        return list(dict.fromkeys(v for v in values if v))

    return {
        "instruments": unique(c.get("instrument_id") for c in constructs),
        "versions": unique(c.get("version_id") for c in constructs),
        "constructs": unique(c.get("construct_id") for c in constructs),
        "frameworks": unique((study.get("design") or {}).get("frameworks") or []),
        "disciplines": unique(study.get("discipline") or []),
        "education_levels": unique((record.get("education") or {}).get("education_levels") or []),
    }


def linking_keywords(record: dict | None) -> list[str]:
    """The HuMeta keywords to add to a deposit, e.g. ``humeta:instrument:gci``."""
    links = study_links(record)
    out = [f"humeta:instrument:{x}" for x in links["instruments"]]
    out += [f"humeta:version:{x}" for x in links["versions"]]
    out += [f"humeta:construct:{x}" for x in links["constructs"]]
    out += [f"humeta:framework:{x}" for x in links["frameworks"]]
    return out


def fetch_index(url: str = DATASET_INDEX_URL, timeout: float = 15) -> dict:
    """The published dataset index. Raises on a network or format problem."""
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "HuMeta-Portal"})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310 (fixed https host)
        index = json.loads(response.read().decode("utf-8"))
    if index.get("format") != "humeta-dataset-index":
        raise ValueError("not a HuMeta dataset index")
    return index


@dataclass
class Match:
    dataset: dict
    score: int
    reasons: list[str] = field(default_factory=list)


def related(index: dict | None, record: dict | None, limit: int = 25) -> list[Match]:
    """Datasets sharing instruments, constructs, theories, disciplines, or education levels with a study, best first.

    A dataset that shares only a discipline or education level is left out: those alone are too broad.
    """
    mine = study_links(record)
    matches = []
    for ds in (index or {}).get("datasets") or []:
        score, reasons, specific = 0, [], False
        for kind, weight in WEIGHTS.items():
            shared = [x for x in mine[kind] if x in (ds.get(kind) or [])]
            if shared:
                score += weight * len(shared)
                reasons.append(f"{len(shared)} {REASONS[kind]}{'s' if len(shared) != 1 else ''}")
                specific = specific or kind in ("instruments", "constructs", "frameworks")
        if specific:
            matches.append(Match(ds, score, reasons))
    matches.sort(key=lambda m: (-m.score, (m.dataset.get("title") or "").lower()))
    return matches[:limit]


def dataset_page(dataset: dict) -> str:
    """The dataset's page on the HuMeta Library website."""
    return f"{DATASETS_PAGE_URL}{dataset['id']}/"
