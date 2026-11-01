import pytest

from oem import codebook, naming
from oem.library import Library, LibraryError


@pytest.fixture(scope="module")
def lib():
    return Library.load()


def test_loads_everything(lib):
    assert "gci" in lib.instruments
    assert lib.items("gci", "gci-v4-2014")
    assert "agree5" in lib.scales
    assert "race_eth" in lib.standard_variables
    assert lib.constructs


def test_unknown_ids_raise(lib):
    with pytest.raises(LibraryError):
        lib.instrument("nope")
    with pytest.raises(LibraryError):
        lib.version("gci", "nope")
    with pytest.raises(LibraryError):
        lib.scale("nope")


def test_prefixes_unique_and_valid(lib):
    prefixes = [lib.prefix(i) for i in lib.instruments]
    assert len(prefixes) == len(set(prefixes))
    assert all(naming.is_valid(p) for p in prefixes)


def test_every_library_variable_name_is_valid_and_unique(lib):
    """Generate variables for every item and standard variable in the library."""
    variables = []
    for (instrument_id, version_id) in lib.item_files:
        variables += codebook.instrument_items(lib, instrument_id, version_id)
    for name in lib.standard_variables:
        variables += codebook.standard_variable(lib, name)
    book = codebook.Codebook(variables)  # raises on duplicates
    assert all(naming.is_valid(n) for n in book.names())


def test_construct_search(lib):
    found = {c["id"] for c in lib.find_constructs("belonging")}
    assert "sense_of_belonging" in found
    instruments = {i["id"] for i in lib.instruments_for_constructs(found)}
    assert "math-sense-of-belonging" in instruments
