"""Kit-author checks; run here, unlike tests_docs/ which runs after install."""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml


KIT = Path(__file__).resolve().parents[1]


def install(target, *options):
    result = subprocess.run(
        [sys.executable, str(KIT / "scripts/install.py"), str(target), *options],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


@pytest.mark.parametrize("workboard", [False, True])
def test_fresh_install_and_rerun(tmp_path, workboard):
    subprocess.run(["git", "init", "-b", "main", str(tmp_path)],
                   capture_output=True, check=True)
    options = ["--with-ci"] + (["--with-workboard"] if workboard else [])
    install(tmp_path, *options)
    if workboard:
        # Use the module, not just its empty skeleton: templates must resolve
        # links both in templates/ and from their documented mailbox paths.
        board = tmp_path / "docs/in_process/workboard"
        for template, mailbox in [("task_card", "tasks"),
                                  ("task_receipt", "receipts"),
                                  ("coordination_notice", "notices")]:
            (board / mailbox / "L1-example.md").write_text(
                (board / "templates" / f"{template}.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
    installed = {p: p.read_bytes() for p in tmp_path.rglob("*")
                 if p.is_file() and ".git" not in p.relative_to(tmp_path).parts}
    assert "copied : 0" in install(tmp_path, *options)
    assert all(p.read_bytes() == contents for p, contents in installed.items())
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/docs/", "-q"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_add_workboard_preserves_existing_maps_and_prints_manual_steps(tmp_path):
    install(tmp_path)
    maps = [tmp_path / "docs/skill/CLAUDE.md", tmp_path / "docs/in_process/CLAUDE.md"]
    for path in maps:
        path.write_text(path.read_text(encoding="utf-8") + "\nLocal instructions.\n",
                        encoding="utf-8")
    before = [path.read_bytes() for path in maps]
    output = install(tmp_path, "--with-workboard")
    assert [path.read_bytes() for path in maps] == before
    assert "ACTION:" in output
    assert "parallel_workboard.md" in output
    assert "Coordinated multi-agent work:" in output
    assert (tmp_path / "docs/in_process/workboard/templates/task_card.md").is_file()


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
