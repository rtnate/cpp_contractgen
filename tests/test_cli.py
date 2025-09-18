import pathlib
import subprocess
import sys

def run_cli(args, cwd):
    result = subprocess.run(
        [sys.executable, "-m", "cpp_contractgen"] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result

def test_cli_single_file(tmp_path):
    infile = tmp_path / "MyComb.hpp.contract"
    infile.write_text("define_contract MyComb { void advance(); };")

    result = run_cli([str(infile)], cwd=tmp_path)
    assert result.returncode == 0

    outfile = tmp_path / "MyComb.contract.hpp"
    assert outfile.exists()
    assert "MyCombWrapper" in outfile.read_text()

def test_cli_search_dir_recursive(tmp_path):
    subdir = tmp_path / "nested"
    subdir.mkdir()
    infile = subdir / "Other.hpp.contract"
    infile.write_text("define_contract Other { void run(); };")

    outdir = tmp_path / "generated"
    result = run_cli(["--search-dir", str(tmp_path), "--outdir", str(outdir), "-r"], cwd=tmp_path)
    assert result.returncode == 0

    outfile = outdir / "nested" / "Other.contract.hpp"
    assert outfile.exists()
    assert "OtherWrapper" in outfile.read_text()
