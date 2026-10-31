import pytest

from oem import naming


@pytest.mark.parametrize("name", ["gci_q05", "race_eth_mena", "belong_01", "a", "x" * 32])
def test_valid_names(name):
    assert naming.is_valid(name)


@pytest.mark.parametrize(
    "name",
    ["", "GCI_q05", "5gci", "gci-q05", "gci q05", "x" * 33, "gci__q05", "gci_", "_gci", "if"],
)
def test_invalid_names(name):
    assert not naming.is_valid(name)
    with pytest.raises(naming.NamingError):
        naming.check(name)


def test_item_and_option_variables():
    assert naming.item_variable("gci", "q39a") == "gci_q39a"
    assert naming.option_variable("gci_q01", "C") == "gci_q01_c"


def test_custom_variable():
    assert naming.custom_variable("Sense of Belonging", 3) == "sense_of_bel_03"
    with pytest.raises(naming.NamingError):
        naming.custom_variable("belonging", 0)


def test_timepoints():
    assert naming.with_timepoint("gci_q05", "pre") == "gci_q05_pre"
    assert naming.with_timepoint("gci_q05", None) == "gci_q05"
    with pytest.raises(naming.NamingError):
        naming.with_timepoint("gci_q05", "before")


def test_slugify_never_starts_with_digit():
    assert naming.is_valid(naming.slugify("2nd year"))


def test_deduplicate_keeps_length_limit():
    long = "x" * 32
    result = naming.deduplicate([long, long, "a", "a"])
    assert len(set(result)) == 4
    assert all(naming.is_valid(n) for n in result)
