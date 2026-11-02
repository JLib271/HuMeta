# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module 5 analyses, organized by the constructs in a variable plan.

Because Module 2 generates shared variable names, a dataset's columns can be
matched to the plan automatically (:func:`match_columns`). Each match is a
*scale*: the variables that measure one construct with one measure at one
timepoint. For each scale we report descriptives, a scale score, and
reliability. Scale scores are then correlated.

Statistics come from **pingouin** (Vallat, 2018), a peer-reviewed open-source
package; this module only prepares the data and tidies the results. The same
analyses can be rerun in R with the script from :func:`r_script`.

Nothing here imports Streamlit. Data passed in are never written anywhere.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from oem import naming
from oem import plan as P
from oem.library import Library

PINGOUIN_CITATION = ("Vallat, R. (2018). Pingouin: statistics in Python. Journal of Open Source Software, 3(31), 1026. "
                     "https://doi.org/10.21105/joss.01026")
PSYCH_CITATION = ("Revelle, W. psych: Procedures for Psychological, Psychometric, and Personality Research [R package]. "
                  "https://CRAN.R-project.org/package=psych")
SCORE_METHODS = {"mean": "Mean of the items", "sum": "Sum of the items"}


@dataclass
class Scale:
    key: str
    construct: str
    measure: str
    timepoint: str | None
    expected: list[str]
    columns: list[str] = field(default_factory=list)
    data_type: str = "numeric"            # numeric, ordinal, categorical, binary
    missing_codes: list[float] = field(default_factory=list)
    values: dict[str, list[tuple[int, str | None]]] = field(default_factory=dict)

    @property
    def label(self) -> str:
        return f"{self.construct}: {self.measure}" + (f" ({self.timepoint})" if self.timepoint else "")

    @property
    def missing(self) -> list[str]:
        found = {c.lower() for c in self.columns}
        return [name for name in self.expected if name.lower() not in found]


# ------------------------------------------------------------------ matching
def scale_groups(lib: Library, plan: dict) -> list[dict]:
    """One group per construct and measure: a library instrument (or subscale) is one scale; all
    researcher-written questions for a construct form one scale, and so do all its codes."""
    merged: dict[tuple, dict] = {}
    for group in P.measure_groups(lib, plan):
        m = group["measure"]
        kind_key = (m["kind"],) if m["kind"] in ("question", "code") else (m["kind"], m.get("instrument_id"), m.get("dimension_id"))
        entry = merged.setdefault((group["construct"]["id"], *kind_key),
                                  {"construct": group["construct"], "label": group["label"], "variables": []})
        entry["variables"] += group["variables"]
    return list(merged.values())


def match_columns(lib: Library, plan: dict, columns: list[str]) -> tuple[list[Scale], list[str], list[str]]:
    """Match dataset columns to the plan's variables by their shared names (case-insensitive).

    Returns (scales, standard-variable columns found, columns not in the plan).
    """
    plan = P.normalize(plan, lib)
    by_lower = {str(c).lower(): c for c in columns}
    used: set[str] = set()
    scales: list[Scale] = []
    for i, entry in enumerate(scale_groups(lib, plan)):
        for tp in plan["timepoints"] or [None]:
            expected = [naming.with_timepoint(v.name, tp) for v in entry["variables"]]
            matched = [by_lower[name.lower()] for name in expected if name.lower() in by_lower]
            used.update(matched)
            types = {v.data_type for v in entry["variables"]}
            codes = sorted({code for v in entry["variables"] for code, _ in v.missing})
            scales.append(Scale(
                key=f"{entry['construct']['id']}|{i}|{tp or ''}", construct=entry["construct"]["label"],
                measure=entry["label"], timepoint=tp, expected=expected, columns=matched,
                data_type="binary" if types == {"binary"} else ("numeric" if types == {"numeric"} else "ordinal"),
                missing_codes=[float(c) for c in codes],
                values={naming.with_timepoint(v.name, tp): list(v.values) for v in entry["variables"] if v.values},
            ))
    standard = []
    for name in plan["standard_variables"]:
        for v in P.codebook.standard_variable(lib, name):
            if v.name.lower() in by_lower:
                standard.append(by_lower[v.name.lower()])
                used.add(by_lower[v.name.lower()])
    unmatched = [c for c in columns if c not in used]
    return scales, standard, unmatched


def manual_scale(name: str, columns: list[str]) -> Scale:
    """A scale the researcher defines by hand (when there is no variable plan)."""
    return Scale(key=f"manual|{name}", construct=name, measure="selected columns", timepoint=None,
                 expected=list(columns), columns=list(columns))


# ------------------------------------------------------------------ data prep
def items(df: pd.DataFrame, scale: Scale) -> pd.DataFrame:
    """The scale's columns as numbers, with missing-data codes (e.g., -99) set to missing."""
    out = df[scale.columns].apply(pd.to_numeric, errors="coerce")
    if scale.missing_codes:
        out = out.mask(out.isin(scale.missing_codes))
    return out


def score(df: pd.DataFrame, scale: Scale, method: str = "mean") -> pd.Series:
    """Scale score per row: mean (or sum) of the available items; missing if every item is missing."""
    data = items(df, scale)
    value = data.mean(axis=1) if method == "mean" else data.sum(axis=1, min_count=1)
    return value.rename(scale.label)


def descriptives(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in data.columns:
        x = pd.to_numeric(data[col], errors="coerce")
        rows.append({"Variable": col, "N": int(x.notna().sum()), "Missing": int(x.isna().sum()),
                     "Mean": x.mean(), "SD": x.std(), "Min": x.min(), "Median": x.median(), "Max": x.max()})
    return pd.DataFrame(rows)


def prevalence(df: pd.DataFrame, scale: Scale) -> pd.DataFrame:
    """For codes (0/1): how often each code is present."""
    data = items(df, scale)
    return pd.DataFrame([{"Code": col, "Units coded": int(data[col].notna().sum()), "Present": int((data[col] == 1).sum()),
                          "Percent present": 100 * data[col].eq(1).sum() / max(int(data[col].notna().sum()), 1)}
                         for col in data.columns])


# ------------------------------------------------------------------ statistics
def _pingouin():
    try:
        import pingouin
    except ImportError as error:  # pragma: no cover - depends on the environment
        raise RuntimeError("The pingouin package is required for reliability and correlations "
                           "(pip install -r requirements.txt).") from error
    return pingouin


def reliability(data: pd.DataFrame) -> dict:
    """Cronbach's alpha with a 95% CI (pingouin), plus corrected item-total correlations and alpha if deleted.

    Uses complete cases (listwise deletion). Needs at least two items and three complete cases.
    """
    complete = data.dropna()
    result = {"items": data.shape[1], "n": int(len(complete)), "alpha": None, "ci_low": None, "ci_high": None,
              "item_stats": pd.DataFrame()}
    if data.shape[1] < 2 or len(complete) < 3:
        return result
    pg = _pingouin()
    alpha, ci = pg.cronbach_alpha(data=complete)
    result.update(alpha=float(alpha), ci_low=float(ci[0]), ci_high=float(ci[1]))
    rows = []
    for col in complete.columns:
        rest = complete.drop(columns=col)
        r = complete[col].corr(rest.sum(axis=1)) if complete[col].std() > 0 else np.nan
        if_deleted = float(pg.cronbach_alpha(data=rest)[0]) if rest.shape[1] >= 2 else np.nan
        rows.append({"Item": col, "Mean": complete[col].mean(), "SD": complete[col].std(),
                     "Corrected item-total r": r, "Alpha if item deleted": if_deleted})
    result["item_stats"] = pd.DataFrame(rows)
    return result


def correlations(scores: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """Pairwise correlations between scale scores with n, r, 95% CI and p (pingouin.pairwise_corr)."""
    usable = scores.loc[:, scores.notna().sum() >= 3]
    if usable.shape[1] < 2:
        return pd.DataFrame()
    raw = _pingouin().pairwise_corr(data=usable, method=method)
    ci_col = next((c for c in raw.columns if str(c).upper().startswith("CI95")), None)
    p_col = next((c for c in raw.columns if str(c).lower().replace("_", "-") in ("p-unc", "p-val")), None)
    out = pd.DataFrame({"Variable 1": raw["X"], "Variable 2": raw["Y"], "n": raw["n"], "r": raw["r"]})
    if ci_col:
        out["95% CI low"] = [float(ci[0]) for ci in raw[ci_col]]
        out["95% CI high"] = [float(ci[1]) for ci in raw[ci_col]]
    if p_col:
        out["p"] = raw[p_col].astype(float)
    return out


def correlation_matrix(scores: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    return scores.corr(method=method)


# ------------------------------------------------------------------ example data
def example_data(lib: Library, plan: dict, n: int = 120, seed: int = 42) -> pd.DataFrame:
    """Synthetic data shaped like the plan's codebook (for trying Module 5; not research data)."""
    rng = np.random.default_rng(seed)
    plan = P.normalize(plan, lib)
    frame: dict[str, np.ndarray] = {"participant_id": np.arange(1, n + 1)}
    for group in scale_groups(lib, plan):
        for tp in plan["timepoints"] or [None]:
            latent = rng.normal(0, 1, n)
            for v in group["variables"]:
                name = naming.with_timepoint(v.name, tp)
                signal = latent + rng.normal(0, 0.8, n)
                if v.data_type == "binary":
                    frame[name] = (signal > 0.3).astype(int)
                elif v.values:
                    codes = np.array(sorted(code for code, _ in v.values))
                    position = np.clip(np.round((signal + 2) / 4 * (len(codes) - 1)), 0, len(codes) - 1).astype(int)
                    frame[name] = codes[position]
                else:
                    frame[name] = np.round(3 + signal, 2)
    return pd.DataFrame(frame)


# ------------------------------------------------------------------ R script
def _r_name(text: str) -> str:
    return "`" + str(text).replace("`", "'") + "`"


def r_script(scales: list[Scale], method: str = "mean", correlation_method: str = "pearson") -> str:
    """An R script (psych package) that reproduces these analyses on the researcher's own computer."""
    usable = [s for s in scales if s.columns]
    codes = sorted({c for s in usable for c in s.missing_codes})
    scale_lines = ",\n".join(f"  {_r_name(s.label)} = c({', '.join(repr(c) for c in s.columns)})" for s in usable)
    combine = "rowMeans" if method == "mean" else "rowSums"
    return f"""# Module 5 analyses from the HuMeta Portal, reproduced in R.
# Run this on your own computer: your data never leave it.
# Uses the psych package: {PSYCH_CITATION}
# install.packages(c("psych", "GPArotation"))   # once
library(psych)

data <- read.csv("YOUR_DATA.csv", check.names = FALSE)   # the same file you analyzed in the portal

# Scales: the variables that measure each construct (from your variable plan)
scales <- list(
{scale_lines}
)

# Missing-data codes from the codebook become NA
missing_codes <- c({', '.join(str(int(c)) for c in codes)})
for (col in unique(unlist(scales))) data[[col]][data[[col]] %in% missing_codes] <- NA

# Descriptives and reliability for each scale
for (name in names(scales)) {{
  items <- data[, scales[[name]], drop = FALSE]
  cat("\\n==========", name, "==========\\n")
  print(describe(items))
  if (ncol(items) >= 2) print(alpha(items, check.keys = FALSE))
  if (ncol(items) >= 3) print(omega(items, nfactors = 1, plot = FALSE))  # omega total
}}

# Scale scores ({SCORE_METHODS.get(method, method).lower()}) and their correlations
scores <- as.data.frame(lapply(scales, function(cols) {combine}(data[, cols, drop = FALSE], na.rm = TRUE)),
                        check.names = FALSE)
print(describe(scores))
if (ncol(scores) >= 2) print(corr.test(scores, method = "{correlation_method}"), short = FALSE)
"""


# ------------------------------------------------------------------ report
def results_tables(scales: list[Scale], reliabilities: dict[str, dict], correlations_table: pd.DataFrame) -> dict[str, pd.DataFrame]:
    rel = pd.DataFrame([{
        "Scale": s.label, "Items": r["items"], "Complete cases": r["n"],
        "Cronbach's alpha": r["alpha"], "95% CI low": r["ci_low"], "95% CI high": r["ci_high"],
    } for s in scales if (r := reliabilities.get(s.key))])
    return {"reliability": rel, "correlations": correlations_table}


def pdf_report(title: str, n_rows: int, scales: list[Scale], score_desc: pd.DataFrame,
               reliabilities: dict[str, dict], correlations_table: pd.DataFrame, method: str) -> bytes:
    """A short PDF of the results tables (reportlab). Contains summary statistics only, no raw data."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=title, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)

    def table(frame: pd.DataFrame) -> Table:
        def cell(v):
            if isinstance(v, (float, np.floating)):
                return "" if np.isnan(v) else f"{v:.3f}"
            return str(v)
        t = Table([list(frame.columns)] + [[cell(v) for v in row] for row in frame.itertuples(index=False)], hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                               ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 7),
                               ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0"))]))
        return t

    story = [Paragraph(title, styles["Title"]),
             Paragraph(f"{n_rows} rows analyzed. Scale scores: {SCORE_METHODS.get(method, method).lower()}. "
                       f"Statistics computed with pingouin ({PINGOUIN_CITATION}).", styles["BodyText"]),
             Spacer(1, 10), Paragraph("Scale scores", styles["Heading2"]), table(score_desc.round(3)), Spacer(1, 10)]
    rel = results_tables(scales, reliabilities, correlations_table)["reliability"]
    if not rel.empty:
        story += [Paragraph("Reliability (Cronbach's alpha, complete cases)", styles["Heading2"]), table(rel), Spacer(1, 10)]
    if not correlations_table.empty:
        story += [Paragraph("Correlations between scale scores", styles["Heading2"]), table(correlations_table)]
    doc.build(story)
    return buffer.getvalue()


def safe_filename(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_") or "results"
