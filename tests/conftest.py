import os
import sys
import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture
def inputdata_root(tmp_path):
    """
    Stage a fake <inputdata> tree so OLMTutils.get_sitegroups/get_site_info
    (which hardcode '<inputdata>/lnd/clm2/PTCLM/...') can find the repo's
    real inputdata/PTCLM/*.txt files without those files having to live
    at that path in the repo itself.

    Returns the path to use as `inputdata` when calling the functions
    under test, e.g. get_site_info(str(inputdata_root), sitegroup='NGEEArctic').
    """
    src = REPO_ROOT / "inputdata" / "PTCLM"
    assert src.is_dir(), f"expected repo inputdata at {src}"

    dest = tmp_path / "lnd" / "clm2" / "PTCLM"
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(src, dest)

    return tmp_path


@pytest.fixture
def olmtutils():
    """Import OLMTutils directly; it only needs numpy, so a plain
    import is safe (no need to dodge model_ELM/__init__.py here)."""
    sys.path.insert(0, str(REPO_ROOT))
    import OLMTutils
    return OLMTutils
