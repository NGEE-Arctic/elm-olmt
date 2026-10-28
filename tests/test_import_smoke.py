import py_compile
import pathlib
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Only files that are both import-safe today and currently touched by the
# NGEE-Arctic PR stack. Deliberately NOT a glob: model_ELM/main.py,
# runscripts/*.py, and several other top-level scripts execute
# module-level side effects (arg parsing, job submission, tkinter/display
# setup) or have pre-existing unrelated breakage, and are excluded on
# purpose rather than "fixed" as a drive-by here. Extend this list only
# in the same commit that introduces a new import-safe file.
ALLOWLIST = [
    "OLMTutils.py",
    "model_surrogate.py",
    "model_ELM/tide_utils.py",
]


@pytest.mark.parametrize("relpath", ALLOWLIST)
def test_module_compiles(relpath):
    py_compile.compile(str(REPO_ROOT / relpath), doraise=True)
