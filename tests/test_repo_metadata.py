from pathlib import Path
import tomllib


def test_project_readme_file_exists() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))

    readme_path = pyproject["project"]["readme"]

    assert (repo_root / readme_path).exists()
