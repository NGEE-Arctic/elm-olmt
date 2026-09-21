"""
Tests for model_ELM/tide_utils.py, added in PR6 (commit e04eeaa,
"Add marsh/coastal features: tide forcing and Alquimia BGC").

process_tide_components() reads a NOAA-format harmonic-constituent CSV
(columns Component,Amplitude,Speed,Phase -- see
examples/NGEEArctic/tide_components_example.csv) and, per component,
shells out to NCO's `ncap2` to append unit-converted tide coefficients
to a clm_params.nc file:
    Amplitude (m)      -> tide_coeff_amp_<i>    (mm)
    Speed (deg/hour)   -> tide_coeff_period_<i> (seconds)
    Phase (deg)        -> tide_coeff_phase_<i>  (radians)
plus one final tide_baseline write.

`ncap2` (and a real clm_params.nc) are not available in CI, so these
tests stub subprocess.run and assert against the exact command strings
it would have been called with -- this exercises the real parsing,
validation, and unit-conversion logic in the function without needing
NCO or netCDF installed.
"""
import re
from unittest.mock import patch

import pytest

NOAA_HEADER = "Component,Amplitude,Speed,Phase\n"


def _write_tide_csv(path, rows):
    """rows: iterable of (component, amplitude_m, speed_deg_per_hr, phase_deg) str tuples."""
    lines = [NOAA_HEADER]
    for row in rows:
        lines.append(",".join(row) + "\n")
    path.write_text("".join(lines))


def _extract_value(cmd):
    """Pull the numeric literal out of an ncap2 command string of the form
    "...= humhol_ht*0+<value>' <param_file> <param_file>"."""
    m = re.search(r"=\s*humhol_ht\*0\+([\d.eE+-]+)'", cmd)
    assert m, f"could not find assigned value in command: {cmd}"
    return float(m.group(1))


def test_missing_tide_components_file_raises_filenotfounderror(tide_utils, tmp_path):
    param_file = tmp_path / "clm_params.nc"
    param_file.write_text("")
    with pytest.raises(FileNotFoundError):
        tide_utils.process_tide_components(
            str(tmp_path / "does_not_exist.csv"), str(param_file)
        )


def test_missing_param_file_raises_filenotfounderror(tide_utils, tmp_path):
    tide_file = tmp_path / "tide_components.csv"
    _write_tide_csv(tide_file, [("M2", "0.10", "30.0", "90.0")])
    with pytest.raises(FileNotFoundError):
        tide_utils.process_tide_components(
            str(tide_file), str(tmp_path / "does_not_exist.nc")
        )


def test_missing_required_column_raises_valueerror(tide_utils, tmp_path):
    tide_file = tmp_path / "tide_components.csv"
    tide_file.write_text("Component,Amplitude,Speed\nM2,0.10,30.0\n")  # no Phase column
    param_file = tmp_path / "clm_params.nc"
    param_file.write_text("")
    with pytest.raises(ValueError):
        tide_utils.process_tide_components(str(tide_file), str(param_file))


def test_single_component_unit_conversions_and_call_count(tide_utils, tmp_path):
    tide_file = tmp_path / "tide_components.csv"
    _write_tide_csv(tide_file, [("M2", "0.10", "30.0", "90.0")])
    param_file = tmp_path / "clm_params.nc"
    param_file.write_text("")

    with patch("subprocess.run") as mock_run:
        tide_utils.process_tide_components(
            str(tide_file), str(param_file), tide_baseline=800.0
        )

    # 3 ncap2 calls for the one component (amp, period, phase) + 1 for baseline
    assert mock_run.call_count == 4
    commands = [call.args[0] for call in mock_run.call_args_list]

    amp_cmd, period_cmd, phase_cmd, baseline_cmd = commands

    assert _extract_value(amp_cmd) == pytest.approx(100.0, rel=1e-5)       # 0.10 m -> 100 mm
    assert _extract_value(period_cmd) == pytest.approx(43200.0, rel=1e-5)  # 360*3600/30 deg/hr -> s
    assert _extract_value(phase_cmd) == pytest.approx(1.570796, rel=1e-5)  # 90 deg -> rad
    assert _extract_value(baseline_cmd) == pytest.approx(800.0, rel=1e-5)

    for cmd in commands:
        assert cmd.startswith("ncap2 -O -s")
        assert str(param_file) in cmd
        # ncap2 is run with the same file as both input and output (in-place update)
        assert cmd.count(str(param_file)) == 2

    assert "tide_coeff_amp_1" in amp_cmd
    assert "tide_coeff_period_1" in period_cmd
    assert "tide_coeff_phase_1" in phase_cmd
    assert "tide_baseline" in baseline_cmd


def test_multiple_components_indices_increment_and_call_count(tide_utils, tmp_path):
    tide_file = tmp_path / "tide_components.csv"
    _write_tide_csv(
        tide_file,
        [
            ("M2", "0.15", "28.984", "145.2"),
            ("S2", "0.08", "30.000", "178.3"),
        ],
    )
    param_file = tmp_path / "clm_params.nc"
    param_file.write_text("")

    with patch("subprocess.run") as mock_run:
        tide_utils.process_tide_components(str(tide_file), str(param_file))

    # 3 calls per component * 2 components + 1 baseline call
    assert mock_run.call_count == 7
    commands = [call.args[0] for call in mock_run.call_args_list]

    assert "tide_coeff_amp_1" in commands[0]
    assert "tide_coeff_period_1" in commands[1]
    assert "tide_coeff_phase_1" in commands[2]
    assert "tide_coeff_amp_2" in commands[3]
    assert "tide_coeff_period_2" in commands[4]
    assert "tide_coeff_phase_2" in commands[5]
    assert "tide_baseline" in commands[6]


def test_subprocess_run_invoked_with_shell_and_check(tide_utils, tmp_path):
    """Pin the shell=True, check=True kwargs -- a regression here would
    silently swallow ncap2 failures instead of raising."""
    tide_file = tmp_path / "tide_components.csv"
    _write_tide_csv(tide_file, [("M2", "0.10", "30.0", "0.0")])
    param_file = tmp_path / "clm_params.nc"
    param_file.write_text("")

    with patch("subprocess.run") as mock_run:
        tide_utils.process_tide_components(str(tide_file), str(param_file))

    for call in mock_run.call_args_list:
        assert call.kwargs.get("shell") is True
        assert call.kwargs.get("check") is True


def test_default_tide_baseline_is_800(tide_utils, tmp_path):
    tide_file = tmp_path / "tide_components.csv"
    _write_tide_csv(tide_file, [("M2", "0.10", "30.0", "0.0")])
    param_file = tmp_path / "clm_params.nc"
    param_file.write_text("")

    with patch("subprocess.run") as mock_run:
        tide_utils.process_tide_components(str(tide_file), str(param_file))

    baseline_cmd = mock_run.call_args_list[-1].args[0]
    assert _extract_value(baseline_cmd) == pytest.approx(800.0, rel=1e-5)
