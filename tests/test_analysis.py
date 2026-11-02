import numpy as np
import pandas as pd
import pytest

from oem import analysis as A
from oem import plan as P
from oem.library import Library


@pytest.fixture(scope="module")
def lib():
    return Library.load()


@pytest.fixture(scope="module")
def plan(lib):
    plan = P.empty_plan()
    plan["frameworks"] = ["sdt"]
    plan["constructs"] = P.framework_constructs(lib, ["sdt"])
    plan["measures"] = [
        {"construct": "sdt.autonomy", "kind": "question", "text": f"Autonomy item {i}", "scale_id": "agree5"} for i in range(1, 5)
    ] + [{"construct": "sdt.competence", "kind": "question", "text": f"Competence item {i}", "scale_id": "agree5"} for i in range(1, 4)
         ] + [{"construct": "sdt.relatedness", "kind": "code", "label": "Mentions friends", "text": "Talks about peers."}]
    plan["standard_variables"] = ["participant_id"]
    plan["timepoints"] = ["pre", "post"]
    return P.normalize(plan)


def alpha_formula(frame):
    x = frame.dropna().to_numpy(float)
    k = x.shape[1]
    return k / (k - 1) * (1 - x.var(axis=0, ddof=1).sum() / x.sum(axis=1).var(ddof=1))


def test_columns_match_the_plan_by_shared_names(lib, plan):
    data = A.example_data(lib, plan, n=50)
    data = data.rename(columns={"autonomy_01_pre": "AUTONOMY_01_PRE"})  # matching ignores case
    data["extra_column"] = 1
    scales, standard, unmatched = A.match_columns(lib, plan, list(data.columns))
    labels = [s.label for s in scales]
    assert "Autonomy: Autonomy (researcher-written items) (pre)" in labels
    pre = next(s for s in scales if s.label.startswith("Autonomy") and s.timepoint == "pre")
    assert pre.columns[0] == "AUTONOMY_01_PRE" and len(pre.columns) == 4 and pre.missing == []
    assert next(s for s in scales if s.construct == "Relatedness").data_type == "binary"
    assert standard == ["participant_id"] and unmatched == ["extra_column"]


def test_missing_codes_scores_and_descriptives(lib, plan):
    scales, _, _ = A.match_columns(lib, plan, ["autonomy_01_pre", "autonomy_02_pre", "autonomy_03_pre", "autonomy_04_pre"])
    scale = next(s for s in scales if s.columns)
    df = pd.DataFrame({"autonomy_01_pre": [1, 2, -99], "autonomy_02_pre": [3, 4, 5],
                       "autonomy_03_pre": [5, -98, 5], "autonomy_04_pre": [1, 2, 3]})
    items = A.items(df, scale)
    assert items.isna().sum().sum() == 2  # -99 and -98 are missing-data codes
    assert A.score(df, scale, "mean").round(3).tolist() == [2.5, 2.667, 4.333]
    assert A.score(df, scale, "sum").tolist() == [10, 8, 13]
    desc = A.descriptives(items)
    assert desc.loc[0, "Missing"] == 1 and desc.loc[0, "N"] == 2


def test_prevalence_for_codes(lib, plan):
    scales, _, _ = A.match_columns(lib, plan, ["code_mentions_friends_pre"])
    scale = next(s for s in scales if s.columns)
    table = A.prevalence(pd.DataFrame({"code_mentions_friends_pre": [1, 0, 1, 1]}), scale)
    assert table.loc[0, "Present"] == 3 and table.loc[0, "Percent present"] == 75


def test_reliability_matches_the_alpha_formula(lib, plan):
    pytest.importorskip("pingouin")
    data = A.example_data(lib, plan, n=200)
    scales, _, _ = A.match_columns(lib, plan, list(data.columns))
    scale = next(s for s in scales if s.label.startswith("Autonomy") and s.timepoint == "pre")
    items = A.items(data, scale)
    rel = A.reliability(items)
    assert rel["alpha"] == pytest.approx(alpha_formula(items), abs=1e-6)
    assert rel["ci_low"] < rel["alpha"] < rel["ci_high"] and rel["alpha"] > 0.6
    assert list(rel["item_stats"].columns) == ["Item", "Mean", "SD", "Corrected item-total r", "Alpha if item deleted"]
    assert A.reliability(items.iloc[:, :1])["alpha"] is None


def test_correlations_between_scale_scores(lib, plan):
    pytest.importorskip("pingouin")
    data = A.example_data(lib, plan, n=150)
    scales, _, _ = A.match_columns(lib, plan, list(data.columns))
    scores = pd.concat([A.score(data, s) for s in scales if s.data_type != "binary"], axis=1)
    table = A.correlations(scores, "pearson")
    assert {"Variable 1", "Variable 2", "n", "r", "95% CI low", "95% CI high", "p"} <= set(table.columns)
    first = table.iloc[0]
    assert first["r"] == pytest.approx(scores[first["Variable 1"]].corr(scores[first["Variable 2"]]), abs=1e-6)
    assert first["95% CI low"] <= first["r"] <= first["95% CI high"]


def test_r_script_reproduces_the_scales(lib, plan):
    data = A.example_data(lib, plan, n=10)
    scales, _, _ = A.match_columns(lib, plan, list(data.columns))
    script = A.r_script(scales, "mean", "spearman")
    assert "library(psych)" in script and "alpha(items" in script and "omega(items" in script
    assert "`Autonomy: Autonomy (researcher-written items) (pre)` = c('autonomy_01_pre'" in script
    assert "missing_codes <- c(-99, -98)" in script and 'method = "spearman"' in script and "rowMeans" in script


def test_pdf_report(lib, plan):
    pytest.importorskip("reportlab")
    data = A.example_data(lib, plan, n=30)
    scales, _, _ = A.match_columns(lib, plan, list(data.columns))
    scores = pd.concat([A.score(data, s) for s in scales if s.data_type != "binary"], axis=1)
    rel = {s.key: {"items": 4, "n": 30, "alpha": 0.8, "ci_low": 0.7, "ci_high": 0.9} for s in scales}
    corr = pd.DataFrame({"Variable 1": ["a"], "Variable 2": ["b"], "n": [30], "r": [0.4], "p": [np.float64(0.03)]})
    pdf = A.pdf_report("Test report", len(data), scales, A.descriptives(scores), rel, corr, "mean")
    assert pdf.startswith(b"%PDF")
