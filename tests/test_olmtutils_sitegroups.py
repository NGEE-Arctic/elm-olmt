import numpy as np
import pytest

EXPECTED_SITES = {
    "AK-SP-K64", "AK-SP-K64G", "AK-BEO", "AK-BEOG", "AK-TL", "AK-CL",
    "AK-TFS", "AK-TFS-IMC", "AK-TFS-UPK", "AK-ICP", "AK-KM64", "AK-K64G",
    "CA-TVC", "SE-ASRS", "NO-BS", "RU-SI",
}


def test_get_sitegroups_finds_ngeearctic(olmtutils, inputdata_root):
    groups = olmtutils.get_sitegroups(str(inputdata_root))
    assert "NGEEArctic" in groups


def test_get_site_info_ngeearctic_has_16_sites(olmtutils, inputdata_root):
    info = olmtutils.get_site_info(str(inputdata_root), sitegroup="NGEEArctic")
    assert set(info.keys()) == EXPECTED_SITES


@pytest.mark.parametrize("sitename", sorted(EXPECTED_SITES))
def test_site_lat_lon_and_soil_ranges(olmtutils, inputdata_root, sitename):
    info = olmtutils.get_site_info(str(inputdata_root), sitegroup="NGEEArctic")
    site = info[sitename]
    assert -90.0 <= site["lat"] <= 90.0
    assert -180.0 <= site["lon"] <= 180.0
    assert site["PCT_SAND"] + site["PCT_CLAY"] <= 100.0
    assert np.sum(site["PCT_NAT_PFT"]) <= 100.0 + 1e-6


def test_site_codes_consistent_across_all_three_files(inputdata_root):
    ptclm = inputdata_root / "lnd" / "clm2" / "PTCLM"

    def site_codes(fname):
        with open(ptclm / fname) as f:
            next(f)
            return {line.split(",")[0].strip() for line in f if line.strip()}

    assert site_codes("NGEEArctic_sitedata.txt") == \
        site_codes("NGEEArctic_pftdata.txt") == \
        site_codes("NGEEArctic_soildata.txt") == \
        EXPECTED_SITES


def test_missing_trailing_newline_corrupts_pft_parse(olmtutils, tmp_path):
    """
    get_site_info uses s[:-1] to strip newlines (OLMTutils.py) rather than
    .rstrip('\\n'). This is safe only because every shipped *_pftdata.txt
    file ends with a trailing newline. This test pins that landmine: a
    pftdata file whose last line lacks a trailing newline gets its last
    field truncated by one character instead of the newline being removed,
    which breaks int() conversion of the PFT index column.
    """
    ptclm = tmp_path / "lnd" / "clm2" / "PTCLM"
    ptclm.mkdir(parents=True)
    (ptclm / "Fake_sitedata.txt").write_text(
        "site_code,name,state,lon,lat,elev,startyear,endyear,alignyear\n"
        "X-1,\"x\",AK,-150.0,65.0,10,1950,2023,1851\n"
    )
    (ptclm / "Fake_pftdata.txt").write_text(
        "site_code, pft_f1, pft_c1, pft_f2, pft_c2, pft_f3, pft_c3, pft_f4, pft_c4, pft_f5, pft_c5\n"
        "X-1, 85.0,12, 15.0,11, 0.0,0, 0.0,0, 0.0,0"
    )
    (ptclm / "Fake_soildata.txt").write_text(
        "site_code,soil_depth,n_layers,layer_depth,layer_sand%,layer_clay%\n"
        "X-1,-999,1,-999,45.0,15.0\n"
    )
    with pytest.raises(ValueError):
        olmtutils.get_site_info(str(tmp_path), sitegroup="Fake")
