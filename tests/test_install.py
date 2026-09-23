"""Kit-author checks; run here, unlike tests_docs/ which runs after install."""

import subprocess
import sys
from pathlib import Path

import yaml


KIT = Path(__file__).resolve().parents[1]


def install(target, *options):
    result = subprocess.run(
        [sys.executable, str(KIT / "scripts/install.py"), str(target), *options],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def test_fresh_install_and_rerun(tmp_path):
    subprocess.run(["git", "init", "-b", "main", str(tmp_path)],
                   capture_output=True, check=True)
    options = ["--with-ci"]
    install(tmp_path, *options)
    installed = {p: p.read_bytes() for p in tmp_path.rglob("*")
                 if p.is_file() and ".git" not in p.relative_to(tmp_path).parts}
    assert "copied : 0" in install(tmp_path, *options)
    assert all(p.read_bytes() == contents for p, contents in installed.items())
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/docs/", "-q"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_initial_branch_push_has_no_invalid_base(tmp_path):
    workflow = yaml.safe_load((KIT / "templates/docs.example.yml").read_text(encoding="utf-8"))
    script = workflow["jobs"]["ownership"]["steps"][-1]["run"]
    script = script.replace(
        "${{ github.event.pull_request.base.sha || github.event.before }}", "0" * 40,
    )
    result = subprocess.run(["bash", "-e", "-c", script], cwd=tmp_path,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Initial branch push" in result.stdout
