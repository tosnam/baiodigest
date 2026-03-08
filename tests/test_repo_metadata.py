from pathlib import Path
import tomllib


def test_project_readme_file_exists() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))

    readme_path = pyproject["project"]["readme"]

    assert (repo_root / readme_path).exists()


def test_readme_mentions_newsletter_fetch_command() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    readme = (repo_root / "README.md").read_text(encoding="utf-8")

    assert "python -m baiodigest.newsletters.fetch" in readme
    assert "Gmail API" in readme
