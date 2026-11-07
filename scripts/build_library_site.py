# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build the HuMeta Library website from ``library/``.

The site is static: one page per instrument, theory or lens, and construct,
a reference page for response scales and standard variables, a search page,
and downloads (the library's JSON records and CSV lists). It reads the library
through ``oem.library.Library``, the same reader the HuMeta Portal uses, so
the site and the app always show the same records.

Item text, item images and answer keys are published only where the
instrument's ``access`` record allows it, the same rules
``scripts/validate_library.py`` enforces.

    python scripts/build_library_site.py            # writes _site/
    python scripts/build_library_site.py --out DIR
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import shutil
import sys
from datetime import date
from html import escape
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from oem import evidence as EV  # noqa: E402
from oem.library import Library  # noqa: E402
from oem.vocab import LIBRARY_SITE_URL, PORTAL_URL  # noqa: E402

ASSETS = REPO / "library_site"
REPO_URL = "https://github.com/JLib271/HuMeta"
COMMONS_URL = "https://stemedplus.hcommons.org/"
CONTRIBUTE_URL = f"{REPO_URL}/blob/main/CONTRIBUTING.md"

# --------------------------------------------------------------- labels
LABELS = {
    # instrument types and respondents
    "concept_inventory": "Concept inventory", "attitude_beliefs_survey": "Attitude and beliefs survey",
    "self_report_scale": "Self-report scale", "observation_protocol": "Observation protocol",
    "interview_protocol": "Interview protocol", "rubric": "Rubric", "performance_task": "Performance task",
    "community_member": "Community members", "student": "Students", "instructor": "Instructors",
    "observer": "Trained observers", "visitor": "Visitors", "family": "Families",
    # education levels and settings
    "k5": "K–5", "middle_school": "Middle school", "high_school": "High school", "two_year_college": "Two-year college",
    "undergraduate": "Undergraduate", "graduate": "Graduate", "faculty": "Faculty", "k12_teachers": "K–12 teachers",
    "general_public": "General public", "formal_classroom": "Formal classroom", "online_course": "Online course",
    "lab": "Laboratory", "informal_museum": "Museum (informal)", "informal_community": "Community (informal)",
    "out_of_school_program": "Out-of-school program",
    # access
    "open_download": "Free download", "free_registration": "Free with registration",
    "restricted_verified_educators": "Restricted to verified educators", "request_from_developer": "Request from the developer",
    "publisher_permission": "Publisher permission needed", "commercial": "Commercial", "unclear": "Unclear",
    "open_license": "Open license", "public_domain": "Public domain", "written_permission": "Written permission",
    # versions
    "fixed_form": "Fixed form (everyone takes the same items)", "item_bank": "Item bank (users assemble subtests)",
    "likert": "Likert", "multiple_choice": "Multiple choice", "multiple_response": "Multiple response",
    "dichotomous": "Dichotomous", "interval_coding": "Interval coding", "rating_scale": "Rating scale",
    "open_response": "Open response", "mixed": "Mixed", "single_response": "Single response",
    "observation_code": "Observation code",
    "sum_or_mean": "Sum or mean", "percent_correct": "Percent correct",
    "percent_favorable_vs_expert": "Percent favorable (agreement with experts)", "code_frequency": "Code frequency",
    "rubric_levels": "Rubric levels", "irt": "Item response theory (IRT)",
    # dimensions
    "empirical_factor": "Empirical factor", "design_category": "Design category", "coding_category": "Coding category",
    # evidence
    "internal_consistency": "Internal consistency", "test_retest": "Test-retest", "inter_rater": "Inter-rater agreement",
    "factor_structure": "Factor structure", "measurement_invariance": "Measurement invariance", "item_bias": "Item bias (DIF)",
    "response_process": "Response process", "test_content": "Test content",
    "relations_to_other_variables": "Relations to other variables", "item_analysis": "Item analysis", "irt_scaling": "IRT scaling",
    "cronbach_alpha": "Cronbach's alpha", "kr20": "KR-20", "mcdonald_omega": "McDonald's omega", "cohen_kappa": "Cohen's kappa",
    "icc": "ICC", "pearson_r": "Pearson r", "cfa_fit": "CFA fit", "rasch_person_reliability": "Rasch person reliability",
    "rasch_item_reliability": "Rasch item reliability", "rasch_separation": "Rasch separation",
    "mantel_haenszel_dif": "Mantel-Haenszel DIF",
    "published": "Published", "platform_derived": "From a study run through the HuMeta Portal",
    "developer_reported": "Reported by the developer",
    # review
    "draft": "Draft", "community_submitted": "Community submitted", "maintainer_reviewed": "Maintainer reviewed",
    "source_verified": "Source verified", "provisional": "Provisional", "approved": "Approved",
    # frameworks
    "theory": "Theory", "lens": "Theoretical lens", "own": "Your own framework", "exploratory": "Exploratory approach",
    "education": "Education", "social_sciences": "Social sciences", "humanities": "Humanities", "arts": "Arts",
    "exact": "exact match", "close": "close match", "related": "related",
    # construct domains
    "identity_social": "Identity and social", "affective_motivational": "Affective and motivational",
    "environment": "Environment", "epistemological": "Epistemological", "cognitive": "Cognitive",
    "behavioral_strategy": "Behavior and strategy", "instructional_practice": "Instructional practice",
    "discipline_general": "General (any discipline)",
    "construct_definition": "Built from a definition of what to measure (no theory named)",
    "practical_need": "Built for a practical or instructional need",
    "not_reported": "Not reported in the sources",
    "sensitive": "Sensitive", "quasi_identifier": "Quasi-identifier", "direct_identifier": "Direct identifier",
}


DEV_SHORT = {"theory": "Theory-based", "construct_definition": "Construct definition", "practical_need": "Practical need",
             "not_reported": "Not reported", "": "Not recorded yet"}
EVID_LABELS = {"reliability": "Has reliability evidence", "validity": "Has validity evidence",
               "multi_sample": "Tested in more than one sample", "independent": "Tested by independent researchers"}

BASIS_HELP = {
    "empirical_factor": "supported by factor analysis",
    "design_category": "a content blueprint, not a validated subscale",
    "coding_category": "a group of observation codes",
}


def label(value: str | None, extra: dict | None = None) -> str:
    if value is None:
        return ""
    if extra and value in extra:
        return extra[value]
    return LABELS.get(value) or value.replace("_", " ").capitalize()


def h(value) -> str:
    return escape("" if value is None else str(value))


def slug(value: str) -> str:
    return value.replace("_", "-")


def doi_link(doi: str | None) -> str:
    return f' <a href="https://doi.org/{h(doi)}">doi:{h(doi)}</a>' if doi else ""


def ext(url: str, text: str | None = None) -> str:
    return (f'<a href="{h(url)}" target="_blank" rel="noopener noreferrer">{h(text or url)}'
            '<span class="vh"> (opens in a new tab)</span></a>')


def status_tag(status: str | None) -> str:
    if not status:
        return ""
    cls = "draft" if status in ("draft", "community_submitted", "provisional") else "ok"
    return f'<span class="tag st {cls}">{h(label(status))}</span>'


# ---------------------------------------------------------------- site
class Site:
    def __init__(self, lib: Library, out: Path, disciplines: dict[str, str]):
        self.lib = lib
        self.out = out
        self.disciplines = disciplines
        self.pages: list[str] = []
        self.today = date.today().isoformat()

    # ---------- urls (relative to the site root)
    @staticmethod
    def url(kind: str, rid: str) -> str:
        return f"{kind}/{slug(rid)}/"

    def disc(self, d: str) -> str:
        return self.disciplines.get(d) or label(d)

    # ---------- page frame
    def write_page(self, rel: str, title: str, body: str, description: str = "", depth: int | None = None) -> None:
        depth = rel.count("/") if depth is None else depth
        root = "../" * depth
        canonical = LIBRARY_SITE_URL + rel
        portal = (f'<li>{ext(PORTAL_URL, "HuMeta Portal")}: describe a study, plan its measures, and export its metadata</li>'
                  if PORTAL_URL else
                  f'<li>HuMeta Portal: describe a study, plan its measures, and export its metadata ({ext(REPO_URL, "on GitHub")})</li>')
        page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{h(title)}{"" if rel == "" else " · HuMeta Library"}</title>
<meta name="description" content="{h(description or 'Research instruments, theories, and constructs for education, social science, and humanities research.')}">
<link rel="canonical" href="{h(canonical)}">
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap">
<a class="brand" href="{root}">HuMeta Library</a>
<nav aria-label="Library sections"><a href="{root}#instrument">Instruments</a> <a href="{root}#theory">Theories and lenses</a> <a href="{root}#construct">Constructs</a> <a href="{root}compare/">Compare instruments</a> <a href="{root}reference/">Scales and variables</a> <a href="{root}about/">About</a></nav>
</div></header>
<main id="main" class="wrap">
{body}
</main>
<footer><div class="wrap">
<p>Library records are licensed <a href="{REPO_URL}/blob/main/library/LICENSE.md">CC BY-SA 4.0</a>; item text carries the license shown on each instrument. Built {self.today} from the <a href="{REPO_URL}/tree/main/library">library folder</a> of the HuMeta repository.</p>
<h2><a href="{COMMONS_URL}">More from STEMEd+ Commons</a></h2>
<ul>
{portal}
<li>{ext("https://jlib271.github.io/STEMEd-Digest/", "STEMEd+ Digest")}: new journal articles, preprints, and dissertations</li>
<li>{ext("https://jlib271.github.io/stemed-funding/", "STEMEd+ Funding")}: open calls and deadlines for STEM+ education</li>
<li>{ext("https://jlib271.github.io/stem-ed-research-programs/", "STEM+ Education Research Graduate Programs")}: where to study STEM+ education research</li>
<li>{ext("https://jlib271.github.io/stemed-jobs/", "STEMEd+ Jobs")}: positions in STEM+ education</li>
</ul>
</div></footer>
<script src="{root}assets/site.js"></script>
</body>
</html>
"""
        path = self.out / rel / "index.html" if not rel.endswith(".html") else self.out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(page, encoding="utf-8")
        if not rel.endswith(".html"):
            self.pages.append(rel)

    def recommend_note(self, what: str) -> str:
        where = (f'the {ext(PORTAL_URL, "HuMeta Portal")} (Module 2, Recommend tabs)' if PORTAL_URL
                 else "the HuMeta Portal (Module 2, Recommend tabs)")
        return (f'<p class="note">Spot a mistake or something missing in this {what}? Suggest a correction in {where}, '
                f'or see {ext(CONTRIBUTE_URL, "how to contribute")}. Suggestions are reviewed before they are added.</p>')

    # ---------- relationships
    def construct_instruments(self, cid: str) -> list[tuple[dict, list[str]]]:
        """(instrument, [dimension names]) for instruments measuring the construct."""
        found = []
        for inst in self.lib.instruments.values():
            dims = [d["name"] for d in inst.get("dimensions", []) if cid in d.get("construct_ids", [])]
            if cid in inst.get("construct_ids", []) or dims:
                found.append((inst, dims))
        return sorted(found, key=lambda x: x[0]["name"].lower())

    def construct_frameworks(self, cid: str) -> list[tuple[dict, dict]]:
        found = []
        for fw in self.lib.frameworks.values():
            for c in fw.get("constructs", []):
                if c.get("shared_construct_id") == cid:
                    found.append((fw, c))
        return sorted(found, key=lambda x: x[0]["label"].lower())

    def clink(self, cid: str, root: str) -> str:
        c = self.lib.constructs.get(cid)
        return f'<a href="{root}{self.url("constructs", cid)}">{h(c["label"])}</a>' if c else h(cid)

    # ---------- instruments
    def instrument_page(self, inst: dict) -> None:
        root = "../../"
        iid = inst["id"]
        access = inst.get("access", {})
        review = inst.get("review", {})
        mapping = inst.get("construct_mapping", {})
        text_ok = bool(access.get("item_text_shareable"))
        key_ok = bool(access.get("answer_key_shareable"))
        title = inst["name"] + (f" ({inst['acronym']})" if inst.get("acronym") else "")
        parts = [f'<p class="crumb"><a href="{root}#instrument">Instruments</a></p>',
                 f'<h1>{h(title)}</h1>',
                 f'<div class="tags"><span class="tag k">{h(label(inst.get("instrument_type")))}</span>{status_tag(review.get("status"))}</div>',
                 f'<p class="lead">{h(inst.get("description"))}</p>']

        facts = [("Respondents", ", ".join(label(r) for r in inst.get("respondent", []))),
                 ("Education levels", ", ".join(label(x) for x in inst.get("education_levels", []))),
                 ("Settings", ", ".join(label(x) for x in inst.get("settings", []))),
                 ("Disciplines", ", ".join(self.disc(d) for d in inst.get("disciplines", []))),
                 ("Variable prefix", f'<code>{h(inst.get("variable_prefix"))}</code>')]
        related = [r for r in inst.get("related_instrument_ids", []) if r in self.lib.instruments]
        if related:
            facts.append(("Related instruments", ", ".join(
                f'<a href="{root}{self.url("instruments", r)}">{h(self.lib.instruments[r]["name"])}</a>' for r in related)))
        parts.append(self.facts(facts, raw_keys={"Variable prefix", "Related instruments"}))

        # how it was developed
        dev = inst.get("development") or {}
        parts.append('<h2 id="development">How it was developed</h2>')
        if dev:
            txt = h(label(dev.get("basis")))
            fws = [f'<a href="{root}{self.url("frameworks", f)}">{h(self.lib.frameworks[f]["label"])}</a>'
                   for f in dev.get("framework_ids", []) if f in self.lib.frameworks]
            if fws:
                txt += ": " + ", ".join(fws)
            if dev.get("theory_named"):
                txt += (", " if fws else ": ") + h(dev["theory_named"])
            parts.append(f"<p>{txt}.</p>" + (f'<p class="note">{h(dev["notes"])}</p>' if dev.get("notes") else ""))
        else:
            parts.append('<p>Not recorded yet.</p>')
        parts.append('<p class="note">A theory is not required: many instruments are built from a clear definition of what '
                     'to measure. What matters for choosing one is the evidence below.</p>')

        # evidence profile
        parts.append(self.evidence_profile(inst, root))

        # what it measures
        parts.append('<h2 id="measures">What it measures</h2>')
        cons = inst.get("construct_ids", [])
        parts.append("<p>" + (", ".join(self.clink(c, root) for c in cons) or "No constructs recorded yet.") + "</p>")
        if mapping:
            parts.append(f'<p class="note">Construct mapping: <strong>{h(label(mapping.get("status")))}</strong>. {h(mapping.get("note"))}</p>')

        # access
        parts.append('<h2 id="access">How to get it</h2>')
        acc = [("Access", label(access.get("access_type"))), ("Terms", access.get("terms_summary"))]
        links = []
        if access.get("download_url"):
            links.append(ext(access["download_url"], "Download from the source"))
        if access.get("terms_url"):
            links.append(ext(access["terms_url"], "Terms of use"))
        if links:
            acc.append(("Links", " · ".join(links)))
        basis = access.get("item_text_basis") or {}
        if text_ok:
            txt = "May be republished"
            if basis:
                txt += f': {h(basis.get("license") or label(basis.get("basis")))}'
            acc.append(("Item text", txt))
        else:
            acc.append(("Item text", "Not republished here; get it from the source"))
        acc.append(("Answer key", "Shared here" if key_ok else "Not shared here"))
        parts.append(self.facts(acc, raw_keys={"Links", "Item text"}))
        if basis.get("evidence"):
            parts.append(f'<details><summary>Basis for republishing item text</summary><p>{h(basis["evidence"])}</p>'
                         + (f'<p>Granted by {h(basis["granted_by"])}, {h(basis.get("granted_on"))}.</p>' if basis.get("granted_by") else "")
                         + "</details>")

        # versions
        versions = inst.get("versions", [])
        if versions:
            parts.append('<h2 id="versions">Versions</h2>')
            rows = []
            for v in versions:
                rf = v.get("response_format", {}) or {}
                fmt = label(rf.get("type"))
                if rf.get("scale_points"):
                    fmt += f", {rf['scale_points']} points"
                if rf.get("anchors"):
                    fmt += f" ({rf['anchors']})"
                if rf.get("notes"):
                    fmt += f". {rf['notes']}"
                sc = v.get("scoring", {}) or {}
                scoring = label(sc.get("method")) + (f". {sc['notes']}" if sc.get("notes") else "")
                items = v.get("item_count")
                if v.get("form_type") == "item_bank" and v.get("subtest_length"):
                    items = f"{items} in the pool; subtests of {v['subtest_length']}"
                cite = v.get("citation") or {}
                rows.append([h(v.get("label")), h(v.get("language")), h(v.get("year")), h(items),
                             h(label(v.get("form_type")) if v.get("form_type") else ""),
                             h(fmt), h(scoring), h(v.get("administration_minutes")),
                             h(cite.get("text")) + doi_link(cite.get("doi"))])
            parts.append(self.table(["Version", "Language", "Year", "Items", "Form", "Response format", "Scoring",
                                     "Minutes", "Citation"], rows, cls="wide"))

        # dimensions
        dims = inst.get("dimensions", [])
        if dims:
            parts.append('<h2 id="dimensions">Subscales and dimensions</h2>')
            parts.append('<p class="note">The basis says why each dimension exists: '
                         + "; ".join(f"<strong>{h(label(k))}</strong>: {h(v)}" for k, v in BASIS_HELP.items()) + ".</p>")
            rows = [[h(d.get("name")), h(label(d.get("basis"))),
                     ", ".join(self.clink(c, root) for c in d.get("construct_ids", [])), h(d.get("item_count"))]
                    for d in dims]
            parts.append(self.table(["Dimension", "Basis", "Constructs", "Items"], rows))

        # evidence
        ev = self.lib.evidence_for(iid)
        parts.append('<h2 id="evidence">Reliability and validity evidence</h2>')
        if ev:
            vlabels = {v["version_id"]: v.get("label", v["version_id"]) for v in versions}
            dlabels = {d["dimension_id"]: d["name"] for d in dims}
            rows = []
            for e in sorted(ev, key=lambda e: (e.get("version_id", ""), dlabels.get(e.get("dimension_id"), ""))):
                st = e.get("statistic", {})
                val = st.get("value")
                stat = label(st.get("name")) + (f" = {val}" if val is not None else "")
                if st.get("notes"):
                    stat += f". {st['notes']}"
                sm = e.get("sample", {})
                sample = ", ".join(x for x in [f"n = {sm['n']}" if sm.get("n") else "n not recorded",
                                               label(sm.get("education_level")) if sm.get("education_level") else "",
                                               sm.get("country") or ""] if x)
                if sm.get("description"):
                    sample += f". {sm['description']}"
                src = e.get("source", {})
                rows.append([h(vlabels.get(e.get("version_id"), e.get("version_id"))),
                             h(dlabels.get(e.get("dimension_id"), "Whole instrument")),
                             h(label(e.get("evidence_type"))), h(stat), h(sample),
                             h(label(src.get("kind"))) + ": " + h(src.get("citation")) + doi_link(src.get("doi")),
                             status_tag((e.get("review") or {}).get("status"))])
            parts.append('<p class="note">Each row is one result, for one version, in one sample. An adapted version is not '
                         'automatically as reliable as the original, so compare samples before relying on a value.</p>')
            parts.append(self.table(["Version", "Part", "Evidence", "Result", "Sample", "Source", "Review"], rows, cls="wide"))
        else:
            parts.append("<p>No evidence records yet.</p>")

        # items
        files = [(vid, rec) for (i, vid), rec in self.lib.item_files.items() if i == iid]
        if files:
            parts.append('<h2 id="items">Items</h2>')
            for vid, rec in sorted(files):
                vlabel = next((v.get("label", vid) for v in versions if v["version_id"] == vid), vid)
                parts.append(self.items_block(inst, vid, vlabel, rec, text_ok, key_ok))

        # review and sources
        if review.get("needs_check"):
            parts.append('<h2 id="open">Open questions</h2><p class="note">Things a reviewer still needs to check in this record.</p><ul>'
                         + "".join(f"<li>{h(q)}</li>" for q in review["needs_check"]) + "</ul>")
        oc = inst.get("original_citation") or {}
        parts.append('<h2 id="sources">Sources</h2>')
        if oc.get("text"):
            parts.append(f'<p><strong>Original citation:</strong> {h(oc["text"])}{doi_link(oc.get("doi"))}'
                         + (f' {ext(oc["url"], "Link")}' if oc.get("url") else "") + "</p>")
        if inst.get("info_sources"):
            parts.append("<p><strong>Information drawn from:</strong></p><ul>"
                         + "".join(f"<li>{ext(u)}</li>" for u in inst["info_sources"]) + "</ul>")
        parts.append(self.record_footer("instrument record", f"data/instruments/{iid}.json", root,
                                         extra=f' · <a href="{root}data/evidence/{iid}.json">Evidence (JSON)</a>' if ev else ""))
        self.write_page(self.url("instruments", iid), title, "\n".join(parts), inst.get("description", ""))

    def items_block(self, inst: dict, vid: str, vlabel: str, rec: dict, text_ok: bool, key_ok: bool) -> str:
        iid = inst["id"]
        items = rec.get("items", [])
        out = [f'<h3>{h(vlabel)} <span class="count">({len(items)} items)</span></h3>']
        if rec.get("source"):
            out.append(f'<p class="note">{h(rec["source"])}</p>')
        has_text = text_ok and any(i.get("stem") for i in items)
        if not has_text:
            rows = [[h(i.get("number")), f'<code>{h(i["item_id"])}</code>', h(label(i.get("response_type"))),
                     h(self.derived(i))] for i in items]
            out.append('<p class="note">Item text is not republished here. The crosswalk lists each item by its stable ID, '
                       'so items line up across versions.</p>')
            out.append(self.table(["No.", "Item ID", "Response type", "Derived from"], rows))
            return "\n".join(out)
        lic = (inst.get("access", {}).get("item_text_basis") or {}).get("license")
        if lic:
            out.append(f'<p class="note">Item text license: {h(lic)}.'
                       + ("" if key_ok else " The answer key is not shared here.") + "</p>")
        out.append(f'<details class="items"><summary>Show all {len(items)} items</summary><ol class="items">')
        fig_dir = Path(rec["_dir"])
        for i in items:
            li = [f'<li id="{h(vid)}-{h(i["item_id"])}"><p class="num">{h(i.get("number"))} '
                  f'<span class="note">({h(label(i.get("response_type")))}; <code>{h(i["item_id"])}</code>)</span></p>']
            if i.get("stem"):
                li.append(f'<p>{h(i["stem"])}</p>')
            for f in i.get("figures", []):
                src = self.copy_figure(iid, fig_dir, f["path"])
                if src:
                    li.append(f'<figure><img src="{h(src)}" alt="{h(f.get("caption") or "Item figure")}" loading="lazy">'
                              + (f'<figcaption>{h(f["caption"])}</figcaption>' if f.get("caption") else "") + "</figure>")
            if i.get("options"):
                pics = any(o.get("image") for o in i["options"])
                li.append(f'<ul class="opts{" pics" if pics else ""}">')
                for o in i["options"]:
                    body = h(o.get("text", ""))
                    if o.get("image"):
                        src = self.copy_figure(iid, fig_dir, o["image"])
                        if src:
                            body += f'<img src="{h(src)}" alt="Option {h(o["label"])}" loading="lazy">'
                    mark = ' <span class="tag ok">correct</span>' if key_ok and o.get("is_correct") else ""
                    li.append(f'<li><span class="ol">{h(o["label"])}.</span> {body}{mark}</li>')
                li.append("</ul>")
            if self.derived(i):
                li.append(f'<p class="note">{h(self.derived(i))}</p>')
            if i.get("notes"):
                li.append(f'<p class="note">Note: {h(i["notes"])}</p>')
            li.append("</li>")
            out.append("".join(li))
        out.append("</ol></details>")
        return "\n".join(out)

    @staticmethod
    def derived(item: dict) -> str:
        d = item.get("derived_from")
        if not d:
            return ""
        return f"From {d['item_id']} ({d['relation'].replace('_', ' ')})" + (f": {d['notes']}" if d.get("notes") else "")

    def copy_figure(self, iid: str, src_dir: Path, rel: str) -> str | None:
        """Copy an item image (only for instruments whose item text is shareable); return its URL from the page."""
        if not self.lib.item_text_allowed(iid):
            return None
        src = (src_dir / rel).resolve()
        if not src.is_file() or src_dir.resolve() not in src.parents:
            return None
        dest = self.out / "instruments" / slug(iid) / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copyfile(src, dest)
        return rel

    # ---------- evidence profile
    def evidence_profile(self, inst: dict, root: str) -> str:
        prof = EV.profile(self.lib, inst["id"])
        out = ['<h2 id="profile">Evidence profile</h2>',
               f'<p class="note">Checked against the library\'s <a href="{root}about/#rubric">reliability and validity rubric</a>. '
               'A criterion counts when the evidence was gathered; for statistics, reported values are shown next to the rubric\'s '
               'guide value, not judged against it. Criteria come from the evidence records below or a reviewer\'s checklist.</p>']
        chips = []
        for kind in ("reliability", "validity", "item_writing"):
            got, total = prof.coverage(kind)
            if total:
                chips.append(f'<span class="chip {"ok" if got else "none"}"><strong>{got} of {total}</strong> '
                             f'{h(EV.KIND_LABELS[kind].lower())} categories</span>')
        chips.append(f'<span class="chip">{prof.samples} sample{"s" if prof.samples != 1 else ""}</span>')
        chips.append(f'<span class="chip {"ok" if prof.independent else "none"}">{prof.independent} independent '
                     f'record{"s" if prof.independent != 1 else ""}</span>')
        out.append('<div class="chips">' + "".join(chips) + "</div>")
        if prof.flags:
            out.append('<div class="cautions"><p><strong>Cautions</strong></p><ul>'
                       + "".join(f"<li>{h(f)}</li>" for f in prof.flags) + "</ul></div>")
        rows = []
        for cat in prof.categories:
            if not cat.applies:
                continue
            met = [c for c in cat.criteria if c.status != "none"]
            if met:
                items = []
                for c in met:
                    mark = {"met": "✓", "partly": "◐", "not_met": "✗"}[c.status]
                    word = {"met": "met", "partly": "partly met", "not_met": "not met"}[c.status]
                    items.append(f'<li class="{c.status}"><span aria-hidden="true">{mark}</span><span class="vh">{word}: </span> '
                                 f'<strong>{h(c.id)}.</strong> {h(c.label)}'
                                 + (f'<span class="note"> ({h(c.detail)})</span>' if c.detail else "") + "</li>")
                cell = '<ul class="crit">' + "".join(items) + "</ul>"
            else:
                cell = '<span class="note">Not reported</span>'
            rows.append([f'<strong>{h(cat.numeral)}.</strong> {h(cat.label)}', h(EV.KIND_LABELS[cat.kind]), cell])
        out.append(self.table(["Category", "Kind", "Criteria with evidence"], rows, cls="profile"))
        review = inst.get("rubric_review") or {}
        if review:
            names = {c["id"]: f'{c["numeral"]}. {c["label"]}' for c in self.lib.rubric}
            first = next(iter(review.values()))
            items = "".join(f'<li><strong>{h(names.get(cat, cat))}</strong> ({h(", ".join(r.get("criteria", [])))}): '
                            f'{h(r.get("notes", ""))} <span class="note">Source: {h(r.get("source"))}</span></li>'
                            for cat, r in review.items())
            out.append(f'<details><summary>Rubric review: sources and notes</summary><ul>{items}</ul>'
                       f'<p class="note">{h(first.get("reviewed_by", ""))}{", " + h(first["reviewed_on"]) if first.get("reviewed_on") else ""}.</p></details>')
        if prof.other_reliability:
            out.append('<p class="note">Also recorded, outside the rubric: '
                       + "; ".join(f'{h(label(e["evidence_type"]))} ({h(e["statistic"].get("notes") or e["statistic"].get("value"))})'
                                   for e in prof.other_reliability) + ".</p>")
        return "\n".join(out)

    def compare_page(self) -> None:
        root = "../"
        cats = [c for c in self.lib.rubric]
        head = ["Instrument", "Type", "Development"] + [f'{c["numeral"]}' for c in cats] + ["Samples", "Independent", "Cautions"]
        rows = []
        for inst in sorted(self.lib.instruments.values(), key=lambda i: i["name"].lower()):
            prof = EV.profile(self.lib, inst["id"])
            cells = [f'<a href="{root}{self.url("instruments", inst["id"])}">{h(inst["name"])}</a>',
                     h(label(inst.get("instrument_type"))),
                     h(DEV_SHORT[(inst.get("development") or {}).get("basis", "")])]
            for cat in prof.categories:
                if not cat.applies:
                    cells.append('<span class="na" title="Does not apply">–</span>')
                    continue
                letters = cat.met_letters
                partly = any(c.status in ("partly", "not_met") for c in cat.criteria)
                if letters:
                    cells.append(f'<span class="cell {"partly" if partly else "met"}" title="{h(cat.label)}: criteria '
                                 f'{h(", ".join(letters))}{" (some values below threshold)" if partly else ""}">'
                                 f'{"All" if len(letters) == len(cat.criteria) and len(letters) > 3 else h("".join(letters))}</span>')
                else:
                    cells.append(f'<span class="cell none" title="{h(cat.label)}: not reported"><span class="vh">not reported</span></span>')
            cells += [str(prof.samples), str(prof.independent), str(len(prof.flags))]
            rel, val = prof.coverage("reliability"), prof.coverage("validity")
            rows.append((cells, {"rel": rel[0], "val": val[0], "samples": prof.samples, "ind": prof.independent,
                                 "name": inst["name"].lower()}))
        th = "".join(f'<th scope="col"{" title=" + chr(34) + h(c["label"]) + chr(34) if i >= 3 and i < 3 + len(cats) else ""}>'
                     f'{h(x)}</th>' for i, (x, c) in enumerate(zip(head, [None] * 3 + cats + [None] * 3)))
        body = "".join("<tr " + " ".join(f'data-{k}="{h(v)}"' for k, v in meta.items()) + ">"
                       + "".join(f"<td>{c}</td>" for c in cells) + "</tr>" for cells, meta in rows)
        legend = "".join(f'<li><strong>{h(c["numeral"])}</strong> {h(c["label"])}</li>' for c in cats)
        parts = ['<h1>Compare instruments</h1>',
                 '<p class="lead">Which kinds of reliability and validity evidence each instrument has, checked against the '
                 f'library\'s <a href="{root}about/#rubric">rubric</a>{" (by " + h(json.loads((self.lib.root / "evidence_rubric.json").read_text(encoding="utf-8")).get("credit", "")) + ")" if json.loads((self.lib.root / "evidence_rubric.json").read_text(encoding="utf-8")).get("credit") else ""}. Letters are the rubric criteria with evidence; a '
                 'blank cell means nothing is recorded yet.</p>',
                 '<p class="note">The library does not combine these into one score: a missing category may mean the work '
                 'was never done, or only that it has not been entered yet. Open an instrument to see the evidence itself.</p>',
                 '<div class="bar"><label for="sort">Sort by</label> <select id="sort"><option value="name">Name</option>'
                 '<option value="val">Validity categories with evidence</option><option value="rel">Reliability categories with evidence</option>'
                 '<option value="samples">Number of samples</option><option value="ind">Independent records</option></select></div>',
                 f'<div class="tbl compare"><table id="compare"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>',
                 f'<h2>Rubric categories</h2><ol class="legend">{legend}</ol>',
                 f'<p class="dl">Download: <a href="{root}data/evidence_profiles.csv">Evidence profiles (CSV)</a> · '
                 f'<a href="{root}data/evidence_rubric.json">Rubric (JSON)</a></p>']
        self.write_page("compare/", "Compare instruments", "\n".join(parts))

    # ---------- frameworks
    def framework_page(self, fw: dict) -> None:
        root = "../../"
        fid = fw["id"]
        cons = {c["id"]: c for c in fw.get("constructs", [])}
        parts = [f'<p class="crumb"><a href="{root}#theory">Theories and lenses</a></p>',
                 f'<h1>{h(fw["label"])}</h1>',
                 '<div class="tags">' + f'<span class="tag k">{h(label(fw.get("kind")))}</span>'
                 + "".join(f'<span class="tag k">{h(label(f))}</span>' for f in fw.get("fields", []))
                 + status_tag(fw.get("status")) + "</div>",
                 f'<p class="lead">{h(fw.get("description"))}</p>']
        if fw.get("status") == "draft":
            parts.append('<p class="note">Draft: the description, constructs, relationships, and links to shared constructs '
                         'still need review by experts in the field.</p>')
        if fw.get("citation") or fw.get("doi"):
            cite = f'<p><strong>Key source:</strong> {h(fw.get("citation"))}{doi_link(fw.get("doi"))}</p>'
            if fw.get("citation_status") == "added":
                cite += '<p class="note">This citation was added by maintainers and still needs a reviewer to confirm it.</p>'
            parts.append(cite)
        if fw.get("disciplines"):
            parts.append(self.facts([("Widely used in", ", ".join(self.disc(d) for d in fw["disciplines"]))]))
        parts.append('<h2 id="constructs">Constructs</h2>')
        if cons:
            rows = []
            for c in cons.values():
                shared = c.get("shared_construct_id")
                rows.append([h(c["label"]),
                             (self.clink(shared, root) + f' <span class="note">({h(label(c.get("shared_construct_match")))})</span>')
                             if shared else '<span class="note">No shared construct yet</span>'])
            parts.append(self.table(["Construct in this theory", "Shared construct"], rows))
        else:
            parts.append("<p>A lens or approach: researchers describe the constructs and ideas they draw from it.</p>")
        if fw.get("paths"):
            parts.append('<h2 id="paths">Expected relationships</h2><ul class="paths">')
            for p in fw["paths"]:
                a = cons.get(p["from"], {}).get("label", p["from"])
                b = cons.get(p["to"], {}).get("label", p["to"])
                parts.append(f'<li>{h(a)} <span aria-hidden="true">→</span><span class="vh"> to </span> {h(b)}'
                             + (f'<span class="note">: {h(p.get("relationship"))}</span>' if p.get("relationship") else "") + "</li>")
            parts.append("</ul>")
        built = sorted((i for i in self.lib.instruments.values()
                        if fid in (i.get("development") or {}).get("framework_ids", [])), key=lambda i: i["name"].lower())
        if built:
            parts.append('<h2 id="built">Instruments built on this theory</h2><ul>'
                         + "".join(f'<li><a href="{root}{self.url("instruments", i["id"])}">{h(i["name"])}</a></li>' for i in built)
                         + "</ul>")
        insts: dict[str, dict] = {}
        for c in cons.values():
            if c.get("shared_construct_id"):
                for inst, _ in self.construct_instruments(c["shared_construct_id"]):
                    insts[inst["id"]] = inst
        if insts:
            parts.append('<h2 id="instruments">Instruments that measure its constructs</h2><p class="note">Candidates only: '
                         'check that an instrument fits how this theory defines the construct.</p><ul>'
                         + "".join(f'<li><a href="{root}{self.url("instruments", i)}">{h(insts[i]["name"])}</a></li>'
                                   for i in sorted(insts, key=lambda k: insts[k]["name"].lower())) + "</ul>")
        parts.append(self.record_footer("theory record", "data/frameworks.json", root))
        self.write_page(self.url("frameworks", fid), fw["label"], "\n".join(parts), fw.get("description", ""))

    # ---------- constructs
    def construct_page(self, c: dict) -> None:
        root = "../../"
        cid = c["id"]
        parts = [f'<p class="crumb"><a href="{root}#construct">Constructs</a></p>',
                 f'<h1>{h(c["label"])}</h1>',
                 f'<div class="tags"><span class="tag k">{h(label(c.get("domain")))}</span></div>',
                 f'<p class="lead">{h(c.get("definition"))}</p>']
        facts = []
        if c.get("synonyms"):
            facts.append(("Also called", ", ".join(c["synonyms"])))
        if c.get("broader"):
            b = c["broader"] if isinstance(c["broader"], list) else [c["broader"]]
            facts.append(("Broader", ", ".join(self.clink(x, root) for x in b)))
        if c.get("eric"):
            facts.append(("ERIC descriptors", ", ".join(c["eric"])))
        if facts:
            parts.append(self.facts(facts, raw_keys={"Broader"}))
        insts = self.construct_instruments(cid)
        parts.append('<h2 id="instruments">Instruments</h2>')
        if insts:
            parts.append("<ul>" + "".join(
                f'<li><a href="{root}{self.url("instruments", i["id"])}">{h(i["name"])}</a>'
                + (f'<span class="note">: {h(", ".join(dims))}</span>' if dims else "") + "</li>" for i, dims in insts) + "</ul>")
        else:
            parts.append("<p>No instruments in the library measure this construct yet.</p>")
        fws = self.construct_frameworks(cid)
        parts.append('<h2 id="theories">Theories that use it</h2>')
        if fws:
            parts.append("<ul>" + "".join(
                f'<li><a href="{root}{self.url("frameworks", f["id"])}">{h(f["label"])}</a>'
                f'<span class="note">: as “{h(fc["label"])}” ({h(label(fc.get("shared_construct_match")))})</span></li>'
                for f, fc in fws) + "</ul>")
        else:
            parts.append("<p>No theories in the library are linked to this construct yet.</p>")
        parts.append(self.record_footer("construct", "data/constructs.json", root))
        self.write_page(self.url("constructs", cid), c["label"], "\n".join(parts), c.get("definition", ""))

    # ---------- reference
    def reference_page(self) -> None:
        root = "../"
        parts = ['<h1>Response scales and standard variables</h1>',
                 '<p class="lead">Shared code lists and fixed variable definitions, so every study codes the same scale '
                 'and the same demographic question the same way.</p>', '<h2 id="scales">Response scales</h2>']
        doc = json.loads((self.lib.root / "scales.json").read_text(encoding="utf-8"))
        if doc.get("missing_codes"):
            parts.append('<p>Missing-value codes used across the library: '
                         + "; ".join(f'<code>{h(m["code"])}</code> {h(m["label"])}' for m in doc["missing_codes"]) + ".</p>")
        for s in self.lib.scales.values():
            parts.append(f'<h3 id="scale-{h(s.id)}">{h(s.label)} <code>{h(s.id)}</code></h3>')
            meta = [label(s.level)]
            if s.reverse_scoring:
                meta.append(f"reverse scoring: {s.reverse_scoring}")
            if s.anchors_only:
                meta.append("only the end points are labeled")
            parts.append(f'<p class="note">{h("; ".join(meta))}</p>')
            parts.append(self.table(["Code", "Label"], [[h(c), h(lbl or "")] for c, lbl in s.points]))
        parts.append('<h2 id="variables">Standard variables</h2>')
        for v in self.lib.standard_variables.values():
            parts.append(f'<h3 id="var-{h(v["name"])}">{h(v["label"])} <code>{h(v["name"])}</code></h3>')
            facts = [("Question", v.get("question")), ("Instruction", v.get("instruction")),
                     ("Data type", label(v.get("data_type"))), ("Unit", v.get("unit")),
                     ("Valid range", f'{v["valid_range"]["min"]}–{v["valid_range"]["max"]}' if v.get("valid_range") else ""),
                     ("Sensitivity", label(v.get("sensitivity"))),
                     ("Source", (h(v.get("source")) + (" " + ext(v["source_url"], "Link") if v.get("source_url") else ""))
                      if v.get("source") else ""), ("Notes", v.get("notes"))]
            parts.append(self.facts(facts, raw_keys={"Source"}))
            if v.get("options"):
                parts.append(self.table(["Code", "Label", "Column suffix"],
                                        [[h(o.get("code")), h(o.get("label")), f'<code>{h(o["suffix"])}</code>' if o.get("suffix") else ""]
                                         for o in v["options"]]))
        parts.append(f'<p class="dl">Download: <a href="{root}data/scales.json">Scales (JSON)</a> · '
                     f'<a href="{root}data/standard_variables.json">Standard variables (JSON)</a></p>')
        self.write_page("reference/", "Response scales and standard variables", "\n".join(parts))

    # ---------- about
    def about_page(self) -> None:
        root = "../"
        n = len(self.lib.instruments), len(self.lib.frameworks), len(self.lib.constructs)
        parts = ['<h1>About the HuMeta Library</h1>',
                 f'<p class="lead">A community-curated library of research instruments ({n[0]}), theories and lenses ({n[1]}), '
                 f'and shared constructs ({n[2]}) for education, social science, and humanities research. It started with '
                 'STEM education research.</p>',
                 '<h2>What is in a record</h2><ul>'
                 '<li><strong>Instruments</strong>: what each one measures, its versions and adaptations, subscales, scoring, '
                 'how to get it, and the reliability and validity evidence reported for it in different samples.</li>'
                 '<li><strong>Theories and lenses</strong>: their constructs, expected relationships, and key source.</li>'
                 '<li><strong>Constructs</strong>: the shared vocabulary that links instruments, theories, and study variables.</li>'
                 '</ul>',
                 '<h2>Review status</h2><p>Every record shows its review status. <strong>Draft</strong> records were entered by '
                 'maintainers and have not yet been checked by experts in the field; many list the open questions a reviewer '
                 'still needs to settle. Construct mappings are <strong>provisional</strong> until a governance committee '
                 'approves them. The library describes instruments; it does not establish that an instrument is valid for '
                 'your study or grant permission to use it.</p>',
                 self.rubric_section(),
                 '<h2>Item text</h2><p>The library describes instruments and never republishes item text unless the instrument\'s '
                 'terms allow it. Even freely downloadable instruments are linked, not copied, unless there is an open license, '
                 'public-domain status, or written permission. Answer keys are shared only where that is allowed too.</p>',
                 '<h2>Downloads</h2><p>Every record is available as JSON, the same files the HuMeta Portal reads. Lists as CSV: '
                 f'<a href="{root}data/instruments.csv">instruments</a>, <a href="{root}data/frameworks.csv">theories and lenses</a>, '
                 f'<a href="{root}data/constructs.csv">constructs</a>, <a href="{root}data/evidence.csv">evidence</a>. '
                 f'The record format is published as JSON Schemas in the {ext(REPO_URL + "/tree/main/library/schema", "library schema folder")}.</p>',
                 '<h2>Contribute</h2>' + self.recommend_note("library").replace('<p class="note">', "<p>"),
                 f'<h2>Cite</h2><p>HuMeta Instrument Library, HuMeta Portal. {h(LIBRARY_SITE_URL)} (accessed {self.today}).</p>']
        self.write_page("about/", "About the HuMeta Library", "\n".join(parts))

    def lib_rubric_credit(self) -> str:
        doc = json.loads((self.lib.root / "evidence_rubric.json").read_text(encoding="utf-8"))
        return doc.get("title", "Reliability and validity rubric") + (f", by {doc['credit']}" if doc.get("credit") else "")

    def rubric_section(self) -> str:
        out = ['<h2 id="rubric">Reliability and validity rubric</h2>',
               f'<p class="note">Rubric: {h(self.lib_rubric_credit())}.</p>',
               '<p>Each instrument\'s evidence profile checks its recorded evidence against this rubric. Instruments do not '
               'need a theory behind them to be included; they need a clear account of what they measure, and the profile '
               'shows how well the evidence supports using them. Item writing categories apply only to multiple-choice or '
               'Likert-type instruments. Numbers in the rubric (alpha > 0.7, item separation > 0.9) are guides, not cut-offs: '
               'the profile records that a value was measured and shows it next to the guide, so readers can judge it in '
               'context.</p>']
        for c in self.lib.rubric:
            out.append(f'<h3>{h(c["numeral"])}. {h(c["label"])} <span class="tag k">{h(EV.KIND_LABELS[c["kind"]])}</span></h3>'
                       f'<p class="note">{h(c["description"])}</p><ul class="rubric">')
            for x in c["criteria"]:
                out.append(f'<li><strong>{h(x["id"])}.</strong> {h(x["label"])}'
                           + (f' <span class="tag k">{h(x["approach"])}</span>' if x.get("approach") else "") + "</li>")
            out.append("</ul>")
        return "".join(out)

    # ---------- home
    def home_page(self, index: list[dict]) -> None:
        kinds = [("instrument", "Instruments"), ("theory", "Theories and lenses"), ("construct", "Constructs")]
        lists = []
        for k, title in kinds:
            items = [r for r in index if r["type"] == k]
            lists.append(f'<section class="all" id="{k}"><h2>{h(title)} <span class="count">({len(items)})</span></h2><ul>'
                         + "".join(f'<li><a href="{h(r["url"])}">{h(r["title"])}</a></li>' for r in items) + "</ul></section>")
        fields = sorted({f for r in index for f in r.get("fields", [])})
        index_json = json.dumps(index, ensure_ascii=False).replace("</", "<\\/")

        def facet_select(key: str, name: str, everything: str, labeller) -> str:
            values = sorted({v for r in index for v in r.get("facets", {}).get(key, []) if v}, key=lambda v: labeller(v).lower())
            if not values:
                return ""
            opts = "".join(f'<option value="{h(v)}">{h(labeller(v))}</option>' for v in values)
            return (f'<div><label for="f-{key}">{h(name)}</label><select id="f-{key}" data-facet="{key}">'
                    f'<option value="">{h(everything)}</option>{opts}</select></div>')

        facets = "".join([facet_select("itype", "Instrument type", "Any type", label),
                          facet_select("resp", "Who responds", "Anyone", label),
                          facet_select("level", "Education level", "Any level", label),
                          facet_select("disc", "Discipline", "Any discipline", self.disc),
                          facet_select("evid", "Evidence", "Any evidence", lambda v: EVID_LABELS.get(v, v)),
                          facet_select("dev", "How it was developed", "Any basis", lambda v: DEV_SHORT.get(v, v))])
        body = f"""<div class="hero">
<h1>HuMeta Library</h1>
<p class="lead">Research instruments, theories, and constructs for education, social science, and humanities research: what each instrument measures, how to get it, and the evidence reported for it.</p>
</div>
<form class="controls" role="search" onsubmit="return false">
<div class="search"><label for="q">Search</label><input id="q" type="search" placeholder="Try belonging, self-efficacy, climate, Rasch…" autocomplete="off"></div>
<div><label for="type">Show</label><select id="type"><option value="">Everything</option><option value="instrument">Instruments</option><option value="theory">Theories and lenses</option><option value="construct">Constructs</option></select></div>
<div><label for="field">Field</label><select id="field"><option value="">All fields</option>{"".join(f'<option value="{h(f)}">{h(label(f))}</option>' for f in fields)}</select></div>
</form>
<fieldset class="controls facets"><legend>Instrument filters <span class="note">(show instruments only)</span></legend>{facets}</fieldset>
<p id="count" class="note" aria-live="polite"></p>
<ol id="results" class="results" hidden></ol>
<div id="browse">
{"".join(lists)}
</div>
<script type="application/json" id="index">{index_json}</script>"""
        self.write_page("", "HuMeta Library", body, depth=0)

    # ---------- shared bits
    @staticmethod
    def facts(rows, raw_keys=frozenset()) -> str:
        out = ['<dl class="facts">']
        for k, v in rows:
            if v:
                out.append(f"<dt>{h(k)}</dt><dd>{v if k in raw_keys else h(v)}</dd>")
        out.append("</dl>")
        return "".join(out)

    @staticmethod
    def table(headers, rows, cls="") -> str:
        keep = [i for i in range(len(headers)) if any(str(r[i]).strip() for r in rows)]
        headers = [headers[i] for i in keep]
        rows = [[r[i] for i in keep] for r in rows]
        head = "".join(f'<th scope="col">{h(x)}</th>' for x in headers)
        body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
        return f'<div class="tbl {cls}"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

    def record_footer(self, what: str, data_path: str, root: str, extra: str = "") -> str:
        return (f'<p class="dl">Download: <a href="{root}{data_path}">This {h(what.split()[0])} data (JSON)</a>{extra}</p>'
                + self.recommend_note(what))

    # ---------- data
    def write_data(self) -> None:
        data = self.out / "data"
        (data / "instruments").mkdir(parents=True, exist_ok=True)
        (data / "evidence").mkdir(parents=True, exist_ok=True)
        for iid, inst in self.lib.instruments.items():
            (data / "instruments" / f"{iid}.json").write_text(json.dumps(inst, indent=2, ensure_ascii=False), encoding="utf-8")
            ev = self.lib.evidence_for(iid)
            if ev:
                (data / "evidence" / f"{iid}.json").write_text(json.dumps(ev, indent=2, ensure_ascii=False), encoding="utf-8")
        for (iid, vid), rec in self.lib.item_files.items():
            clean = {k: v for k, v in rec.items() if not k.startswith("_")}
            dest = data / "items" / iid / f"{vid}.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(clean, indent=2, ensure_ascii=False), encoding="utf-8")
        for name in ("frameworks.json", "constructs.json", "scales.json", "standard_variables.json"):
            shutil.copyfile(self.lib.root / name, data / name)

        def write_csv(name, header, rows):
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(header)
            w.writerows(rows)
            (data / name).write_text(buf.getvalue(), encoding="utf-8")

        write_csv("instruments.csv",
                  ["id", "name", "acronym", "type", "constructs", "respondents", "education_levels", "access", "item_text_shareable",
                   "versions", "evidence_records", "review_status", "page"],
                  [[i["id"], i["name"], i.get("acronym", ""), i.get("instrument_type", ""), ";".join(i.get("construct_ids", [])),
                    ";".join(i.get("respondent", [])), ";".join(i.get("education_levels", [])),
                    i.get("access", {}).get("access_type", ""), bool(i.get("access", {}).get("item_text_shareable")),
                    len(i.get("versions", [])), len(self.lib.evidence_for(i["id"])), i.get("review", {}).get("status", ""),
                    LIBRARY_SITE_URL + self.url("instruments", i["id"])] for i in self.lib.instruments.values()])
        write_csv("frameworks.csv", ["id", "label", "kind", "fields", "status", "citation", "doi", "constructs", "page"],
                  [[f["id"], f["label"], f.get("kind", ""), ";".join(f.get("fields", [])), f.get("status", ""),
                    f.get("citation", ""), f.get("doi", ""), ";".join(c["label"] for c in f.get("constructs", [])),
                    LIBRARY_SITE_URL + self.url("frameworks", f["id"])] for f in self.lib.frameworks.values()])
        write_csv("constructs.csv", ["id", "label", "domain", "definition", "synonyms", "eric", "page"],
                  [[c["id"], c["label"], c.get("domain", ""), c.get("definition", ""), ";".join(c.get("synonyms", [])),
                    ";".join(c.get("eric", [])), LIBRARY_SITE_URL + self.url("constructs", c["id"])]
                   for c in self.lib.constructs.values()])
        shutil.copyfile(self.lib.root / "evidence_rubric.json", data / "evidence_rubric.json")
        prof_rows = []
        for i in self.lib.instruments.values():
            prof = EV.profile(self.lib, i["id"])
            row = [i["id"], i["name"], (i.get("development") or {}).get("basis", "")]
            row += ["n/a" if not c.applies else "".join(c.met_letters) for c in prof.categories]
            row += [prof.samples, prof.independent, " | ".join(prof.flags)]
            prof_rows.append(row)
        write_csv("evidence_profiles.csv",
                  ["id", "name", "development_basis"] + [f"{c['numeral']} {c['label']}" for c in self.lib.rubric]
                  + ["samples", "independent_records", "cautions"], prof_rows)
        write_csv("evidence.csv",
                  ["id", "instrument_id", "version_id", "dimension_id", "evidence_type", "statistic", "value", "sample_n",
                   "education_level", "country", "source_kind", "citation", "doi", "review_status"],
                  [[e["id"], e.get("instrument_id"), e.get("version_id"), e.get("dimension_id", ""), e.get("evidence_type"),
                    e.get("statistic", {}).get("name"), e.get("statistic", {}).get("value"), e.get("sample", {}).get("n"),
                    e.get("sample", {}).get("education_level", ""), e.get("sample", {}).get("country", ""),
                    e.get("source", {}).get("kind"), e.get("source", {}).get("citation", ""), e.get("source", {}).get("doi", ""),
                    (e.get("review") or {}).get("status", "")] for e in self.lib.evidence])

    def index_records(self) -> list[dict]:
        out = []
        for i in sorted(self.lib.instruments.values(), key=lambda x: x["name"].lower()):
            words = [i.get("acronym", ""), i.get("description", ""), label(i.get("instrument_type"))]
            words += [self.lib.constructs[c]["label"] for c in i.get("construct_ids", []) if c in self.lib.constructs]
            words += [d["name"] for d in i.get("dimensions", [])]
            out.append({"type": "instrument", "title": i["name"] + (f" ({i['acronym']})" if i.get("acronym") else ""),
                        "url": self.url("instruments", i["id"]), "kind": label(i.get("instrument_type")),
                        "status": label(i.get("review", {}).get("status")), "summary": i.get("description", ""),
                        "fields": ["education"], "text": " ".join(words),
                        "facets": {"itype": [i.get("instrument_type", "")], "resp": i.get("respondent", []),
                                   "level": i.get("education_levels", []), "disc": i.get("disciplines", []),
                                   "evid": EV.profile(self.lib, i["id"]).tags,
                                   "dev": [(i.get("development") or {}).get("basis", "")]}})
        for f in sorted(self.lib.frameworks.values(), key=lambda x: x["label"].lower()):
            if f.get("kind") in ("own", "exploratory"):
                continue
            words = [f.get("description", ""), f.get("citation", "")] + [c["label"] for c in f.get("constructs", [])]
            out.append({"type": "theory", "title": f["label"], "url": self.url("frameworks", f["id"]),
                        "kind": label(f.get("kind")), "status": label(f.get("status")), "summary": f.get("description", ""),
                        "fields": f.get("fields", []), "text": " ".join(words)})
        for c in sorted(self.lib.constructs.values(), key=lambda x: x["label"].lower()):
            fields = sorted({x for fw, _ in self.construct_frameworks(c["id"]) for x in fw.get("fields", [])}
                            | ({"education"} if self.construct_instruments(c["id"]) else set()))
            out.append({"type": "construct", "title": c["label"], "url": self.url("constructs", c["id"]),
                        "kind": label(c.get("domain")), "status": "", "summary": c.get("definition", ""),
                        "fields": fields, "text": " ".join([c.get("definition", "")] + c.get("synonyms", []) + c.get("eric", []))})
        return out

    def build(self) -> None:
        if self.out.exists():
            shutil.rmtree(self.out)
        self.out.mkdir(parents=True)
        shutil.copytree(ASSETS, self.out / "assets")
        (self.out / ".nojekyll").write_text("", encoding="utf-8")
        for inst in self.lib.instruments.values():
            self.instrument_page(inst)
        for fw in self.lib.frameworks.values():
            if fw.get("kind") not in ("own", "exploratory"):
                self.framework_page(fw)
        for c in self.lib.constructs.values():
            self.construct_page(c)
        self.compare_page()
        self.reference_page()
        self.about_page()
        self.home_page(self.index_records())
        self.write_page("404.html", "Page not found",
                        '<h1>Page not found</h1><p>That record may have been renamed. '
                        f'<a href="{LIBRARY_SITE_URL}">Search the library</a>.</p>', depth=0)
        self.write_data()
        urls = "".join(f"<url><loc>{h(LIBRARY_SITE_URL + p)}</loc></url>" for p in self.pages)
        (self.out / "sitemap.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
            encoding="utf-8")
        (self.out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {LIBRARY_SITE_URL}sitemap.xml\n", encoding="utf-8")


def discipline_labels() -> dict[str, str]:
    vocab = json.loads((REPO / "standard" / "humeta" / "vocabularies.json").read_text(encoding="utf-8"))
    return {t["id"]: t["label"] for t in vocab["vocabularies"]["discipline"]["terms"]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=REPO / "_site")
    ap.add_argument("--library", type=Path, default=None, help="library folder (default: library/)")
    args = ap.parse_args(argv)
    site = Site(Library.load(args.library), args.out, discipline_labels())
    site.build()
    print(f"Built {len(site.pages)} pages in {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
