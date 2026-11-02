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
    assert standard == ["participant_id"] and unmatched == ["example_group", "extra_column"]


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


@pytest.fixture(scope="module")
def frame():
    rng = np.random.default_rng(7)
    n = 90
    group = np.repeat(["a", "b", "c"], n // 3)
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    y = 1 + 0.6 * x1 - 0.3 * x2 + (group == "c") * 0.8 + rng.normal(0, 1, n)
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2, "group": group, "two": np.where(group == "a", "a", "b"),
                         "pre": y, "post": y + 0.4 + rng.normal(0, 0.5, n), "yes": (y > 1).astype(int),
                         "cat": rng.choice(["p", "q"], n)})


def test_compare_two_groups_matches_scipy(frame):
    pytest.importorskip("pingouin")
    from scipy import stats
    res = A.compare_groups(frame["y"], frame["two"])
    welch = res["tests"].iloc[0]
    ref = stats.ttest_ind(frame.loc[frame.two == "a", "y"], frame.loc[frame.two == "b", "y"], equal_var=False)
    assert welch["Test"] == "Welch's t-test"
    assert welch["Statistic"] == pytest.approx(ref.statistic, abs=1e-6) and welch["p"] == pytest.approx(ref.pvalue, abs=1e-6)
    assert list(res["descriptives"]["Group"]) == ["a", "b"] and "Cohen's d" in res["summary"]


def test_compare_three_groups_matches_scipy(frame):
    pytest.importorskip("pingouin")
    from scipy import stats
    res = A.compare_groups(frame["y"], frame["group"])
    tests = res["tests"].set_index("Test")
    groups = [g["y"] for _, g in frame.groupby("group")]
    assert tests.loc["One-way ANOVA", "Statistic"] == pytest.approx(stats.f_oneway(*groups).statistic, abs=1e-6)
    assert tests.loc["Kruskal-Wallis H", "Statistic"] == pytest.approx(stats.kruskal(*groups).statistic, abs=1e-6)
    assert len(res["posthoc"]) == 3 and {"A", "B", "p"} <= set(res["posthoc"].columns)


def test_paired_comparison_matches_scipy(frame):
    pytest.importorskip("pingouin")
    from scipy import stats
    res = A.compare_paired(frame["pre"], frame["post"])
    t = res["tests"].iloc[0]
    ref = stats.ttest_rel(frame["post"], frame["pre"])
    assert t["Statistic"] == pytest.approx(ref.statistic, abs=1e-6) and t["p"] == pytest.approx(ref.pvalue, abs=1e-6)
    assert res["descriptives"].iloc[2]["Mean"] == pytest.approx((frame["post"] - frame["pre"]).mean())


def test_chi_square_matches_scipy(frame):
    pytest.importorskip("pingouin")
    from scipy import stats
    res = A.association(frame["group"], frame["cat"])
    chi2, p, dof, _ = stats.chi2_contingency(pd.crosstab(frame["group"], frame["cat"]))
    row = res["tests"].iloc[0]
    assert row["Chi-square"] == pytest.approx(chi2, abs=1e-6) and row["df"] == dof and row["p"] == pytest.approx(p, abs=1e-6)
    assert 0 <= row["Cramer's V"] <= 1


def test_linear_regression_matches_least_squares(frame):
    pytest.importorskip("pingouin")
    res = A.regression(frame, "y", ["x1", "x2", "group"])
    table = res["coefficients"].set_index("Term")
    X = np.column_stack([np.ones(len(frame)), frame.x1, frame.x2, frame.group == "b", frame.group == "c"]).astype(float)
    b, *_ = np.linalg.lstsq(X, frame["y"].to_numpy(), rcond=None)
    assert list(table.index) == ["Intercept", "x1", "x2", "group_b", "group_c"]  # 'a' is the reference group
    assert table["B"].to_numpy() == pytest.approx(b, abs=1e-6)
    resid = frame["y"] - X @ b
    assert res["model"]["r2"] == pytest.approx(1 - (resid ** 2).sum() / ((frame.y - frame.y.mean()) ** 2).sum(), abs=1e-6)


def test_logistic_regression(frame):
    pytest.importorskip("pingouin")
    res = A.regression(frame, "yes", ["x1"], logistic=True)
    row = res["coefficients"].set_index("Term").loc["x1"]
    assert row["B"] > 0 and row["Odds ratio"] == pytest.approx(np.exp(row["B"]))
    assert res["model"]["n"] == len(frame)


def test_r_script_includes_chosen_tests():
    tests = [{"type": "groups", "outcome": "Score (pre)", "group": "site"},
             {"type": "paired", "before": "Score (pre)", "after": "Score (post)"},
             {"type": "chisq", "x": "code_a", "y": "site"},
             {"type": "regression", "outcome": "passed", "predictors": ["Score (pre)", "site"], "logistic": True}]
    script = A.r_script([], "mean", "pearson", tests)
    for snippet in ["t.test(y ~ g", "oneway.test", "kruskal.test", "paired = TRUE", "chisq.test(tab)",
                    "family = binomial", "confint(fit)", 'v("Score (pre)")']:
        assert snippet in script
    assert "Comparisons and regression" not in A.r_script([], "mean", "pearson")
