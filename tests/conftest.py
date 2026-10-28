import importlib.util
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


@pytest.fixture
def tide_utils():
    """Load model_ELM/tide_utils.py directly from its file path rather
    than `import model_ELM.tide_utils`. The latter would run
    model_ELM/__init__.py (`from .main import *`), which imports
    model_ELM/main.py and model_ELM/makepointdata.py -- pulling in
    optional runtime deps (e.g. geopy) and module-level CIME-oriented
    side effects that are unrelated to tide_utils.py itself and are
    deliberately excluded from tests/test_import_smoke.py's ALLOWLIST.
    tide_utils.py only needs stdlib (csv/os/subprocess), so a direct,
    package-independent load is safe and sufficient here."""
    path = REPO_ROOT / "model_ELM" / "tide_utils.py"
    spec = importlib.util.spec_from_file_location("tide_utils", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
