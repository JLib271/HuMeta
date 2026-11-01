import csv
import io
import json

import pytest

from oem import codebook, naming
from oem.library import Library


@pytest.fixture(scope="module")
def lib():
    return Library.load()


def test_single_response_item(lib):
    [v] = codebook.instrument_items(lib, "gci", "gci-v4-2014", ["q05"])
    assert v.name == "gci_q05"
    assert v.data_type == "categorical"
    assert [code for code, _ in v.values] == list(range(1, len(v.values) + 1))
    assert v.question  # GCI item text is licensed for the library


def test_multiple_response_item_expands_to_options(lib):
    variables = codebook.instrument_items(lib, "gci", "gci-v4-2014", ["q01"])
    assert [v.name for v in variables] == ["gci_q01_a", "gci_q01_b", "gci_q01_c", "gci_q01_d", "gci_q01_e"]
    assert all(v.scale_id == "selected" for v in variables)


def test_no_answer_keys_in_codebook(lib):
    variables = codebook.instrument_items(lib, "gci", "gci-v4-2014")
    text = codebook.Codebook(variables).to_json()
    assert "is_correct" not in text


def test_timepoints_make_distinct_names(lib):
    pre = codebook.instrument_items(lib, "climate-change-concept-inventory", "ccci-2018", ["q03"], timepoint="pre")
    post = codebook.instrument_items(lib, "climate-change-concept-inventory", "ccci-2018", ["q03"], timepoint="post")
    assert pre[0].name == "ccci_q03_pre" and post[0].name == "ccci_q03_post"
    assert len(codebook.Codebook(pre + post)) == 2


def test_duplicate_names_rejected(lib):
    a = codebook.instrument_items(lib, "gci", "gci-v4-2014", ["q05"])
    b = codebook.instrument_items(lib, "gci", "gci-v4-2014", ["q05"])
    with pytest.raises(naming.NamingError):
        codebook.Codebook(a + b)


def test_unknown_item_rejected(lib):
    with pytest.raises(KeyError):
        codebook.instrument_items(lib, "gci", "gci-v4-2014", ["q12"])  # removed from the GCI


def test_race_ethnicity_follows_spd15(lib):
    variables = codebook.standard_variable(lib, "race_eth")
    names = [v.name for v in variables]
    assert names[:7] == ["race_eth_aian", "race_eth_asian", "race_eth_black", "race_eth_hisp",
                         "race_eth_mena", "race_eth_nhpi", "race_eth_white"]
    assert all(v.sensitivity == "sensitive" for v in variables)


def test_sensitive_variables_flagged(lib):
    variables = codebook.standard_variable(lib, "participant_id") + codebook.standard_variable(lib, "course_level")
    book = codebook.Codebook(variables)
    assert [v.name for v in book.sensitive()] == ["participant_id"]


def test_csv_and_json_exports(lib):
    variables = codebook.standard_variable(lib, "consent_share") + codebook.instrument_items(
        lib, "climate-change-concept-inventory", "ccci-2018", ["q05"])
    book = codebook.Codebook(variables)
    rows = list(csv.DictReader(io.StringIO(book.to_csv())))
    assert rows[0]["name"] == "consent_share"
    assert rows[0]["values"] == "0=No; 1=Yes"
    doc = json.loads(book.to_json())
    assert doc["format"] == "openedmetadata-codebook"
    assert [v["name"] for v in doc["variables"]][:2] == ["consent_share", "ccci_q05_a"]
