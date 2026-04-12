from pathlib import Path

from p4_replay.bootstrap import get_repo_root, prepare_notebook


def test_get_repo_root_points_at_this_repo():
    root = Path(__file__).resolve().parents[1]
    assert get_repo_root(root) == root
    assert (root / "config" / "harness_settings.json").is_file()


def test_prepare_notebook_returns_repo_root():
    root = Path(__file__).resolve().parents[1]
    assert prepare_notebook(engine_on_path=True) == root
    assert str(root / "engine") in __import__("sys").path
