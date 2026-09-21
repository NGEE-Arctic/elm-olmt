"""
Tests for the Arctic/permafrost diagnostic variable list added in PR5
(commit 8c40ce4, "Add Arctic diagnostic output variables").

PR5 adds a new, no-argument function get_arctic_diag_vars() to
OLMTutils.py, alongside (not replacing) the pre-existing
get_default_diag_vars(nutrients, use_fates). It does not modify
get_default_diag_vars at all, so we also pin that function's pre-PR5
behavior here to catch any accidental regression.
"""

# Permafrost-specific diagnostics (active layer, water table, soil ice/
# liquid, snow depth) that PR5 introduces and that are not present in
# get_default_diag_vars.
ARCTIC_SPECIFIC_VARS = {
    "ALT", "ALTMAX", "SNOW_DEPTH", "SOILICE", "SOILLIQ", "ZWT", "ZWT_PERCH",
}

# Full expected return value of get_arctic_diag_vars(), per the PR5 diff.
EXPECTED_ARCTIC_DIAG_VARS = [
    "ALT", "ALTMAX", "SNOW_DEPTH", "SOILICE", "SOILLIQ", "ZWT", "ZWT_PERCH",
    "GPP", "NPP", "NEE", "ER", "TLAI", "QVEGT", "FSH", "EFLX_LH_TOT", "TSA",
    "TSOI",
]


def test_get_arctic_diag_vars_matches_expected_list(olmtutils):
    assert olmtutils.get_arctic_diag_vars() == EXPECTED_ARCTIC_DIAG_VARS


def test_get_arctic_diag_vars_contains_permafrost_specific_vars(olmtutils):
    result = set(olmtutils.get_arctic_diag_vars())
    assert ARCTIC_SPECIFIC_VARS.issubset(result)


def test_get_arctic_diag_vars_no_duplicates(olmtutils):
    result = olmtutils.get_arctic_diag_vars()
    assert len(result) == len(set(result))


def test_get_arctic_diag_vars_all_nonempty_strings(olmtutils):
    result = olmtutils.get_arctic_diag_vars()
    assert len(result) > 0
    for var in result:
        assert isinstance(var, str)
        assert len(var) > 0


def test_get_default_diag_vars_still_present_and_unchanged(olmtutils):
    """PR5 does not touch get_default_diag_vars; pin its pre-PR5 return
    values so a future accidental edit (e.g. during a merge/rebase) is
    caught."""
    assert olmtutils.get_default_diag_vars("none", False) == [
        "TLAI", "FPSN", "QVEGT", "QVEGE", "QSOIL", "EFLX_LH_TOT", "FSH",
        "SNOWDP", "QRUNOFF", "QDRAI", "QOVER",
    ]
    assert olmtutils.get_default_diag_vars("npk", False) == [
        "NEE", "NBP", "TLAI", "TOTSOMC", "CWDC", "TOTLITC", "TOTECOSYSC",
        "NPP", "GPP", "QVEGT", "QVEGE", "EFLX_LH_TOT",
    ]


def test_get_default_diag_vars_no_duplicates(olmtutils):
    for nutrients in ("none", "npk"):
        result = olmtutils.get_default_diag_vars(nutrients, False)
        assert len(result) == len(set(result))
