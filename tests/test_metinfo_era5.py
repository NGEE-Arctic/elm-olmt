"""
Tests for metinfo.txt (repo root), which maps a forcing-dataset "mettype"
key to a relative path under <inputdata>. PR3 added the `era5:` entry.

model_ELM/main.py's ELMcase.get_forcing() is the sole consumer of this
file, but it is not a standalone, import-safe function -- it's an inline
block inside a method on a class whose module has module-level side
effects and is deliberately excluded from tests/test_import_smoke.py's
ALLOWLIST. Rather than importing model_ELM.main here, we pin down the
exact parsing rule it uses (from model_ELM/main.py, ELMcase.get_forcing):

    for s in metinfo:
        if s.split(':')[0] == mettype:
            self.metdir = self.inputdata_path + '/' + s.split(':')[1].strip()

and apply that same rule to the real, on-disk metinfo.txt (read-only --
no temp copy needed since we never write to it).
"""
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
METINFO_PATH = REPO_ROOT / "metinfo.txt"


def _lookup_mettype(lines, mettype):
    """Mirror ELMcase.get_forcing()'s lookup exactly (model_ELM/main.py)."""
    match = None
    for s in lines:
        if s.split(":")[0] == mettype:
            match = s.split(":")[1].strip()
    return match


def _data_lines(lines):
    """Non-comment, non-blank lines -- the ones get_forcing() actually
    iterates meaningfully (comment lines never equal a mettype, but we
    still want to validate their formatting below)."""
    return [line for line in lines if line.strip() and not line.strip().startswith("#")]


def test_metinfo_file_exists():
    assert METINFO_PATH.is_file(), f"expected {METINFO_PATH} to exist"


def test_era5_key_present_with_sensible_path():
    lines = METINFO_PATH.read_text().splitlines()
    path = _lookup_mettype(lines, "era5")

    assert path is not None, "expected an 'era5:' entry in metinfo.txt"
    assert "era5" in path.lower(), f"era5 path {path!r} doesn't look era5-related"
    assert not path.startswith("/"), f"era5 path {path!r} should be relative, not absolute"
    assert " " not in path, f"era5 path {path!r} contains unexpected whitespace"
    assert path == path.strip(), f"era5 path {path!r} has leading/trailing whitespace"


def test_gswp3_default_key_still_present():
    """Guard against the era5 addition accidentally clobbering the
    pre-existing default entry that get_forcing() falls back to."""
    lines = METINFO_PATH.read_text().splitlines()
    path = _lookup_mettype(lines, "gswp3")
    assert path is not None, "expected the pre-existing 'gswp3:' entry to remain in metinfo.txt"
    assert path.startswith("atm/datm7/")


def test_all_entries_are_single_colon_key_value_pairs():
    """Catch formatting regressions: every non-comment, non-blank line
    must be a `key: value` pair with exactly one ':' separating a
    non-empty key from a non-empty value (get_forcing() only ever reads
    parts [0] and [1], so a stray extra ':' would silently truncate the
    path instead of raising an error)."""
    lines = METINFO_PATH.read_text().splitlines()
    for line in _data_lines(lines):
        assert line.count(":") == 1, f"expected exactly one ':' in line {line!r}"
        key, value = line.split(":")
        assert key.strip() != "", f"empty key in line {line!r}"
        assert value.strip() != "", f"empty value in line {line!r}"
