from pathlib import Path

from baiodigest.config import Settings


def test_site_prefix_defaults_to_project_pages_prefix(monkeypatch) -> None:
    monkeypatch.delenv("BAIODIGEST_SITE_PREFIX", raising=False)

    settings = Settings()

    assert settings.site_prefix == "/baiodigest"


def test_site_prefix_normalization(monkeypatch) -> None:
    monkeypatch.setenv("BAIODIGEST_SITE_PREFIX", "baiodigest/")
    assert Settings().site_prefix == "/baiodigest"

    monkeypatch.setenv("BAIODIGEST_SITE_PREFIX", "/")
    assert Settings().site_prefix == ""

    monkeypatch.setenv("BAIODIGEST_SITE_PREFIX", "")
    assert Settings().site_prefix == ""


def test_queries_loaded_from_default_file() -> None:
    settings = Settings()

    assert settings.queries_file.name == "queries.toml"
    assert len(settings.pubmed_queries) >= 1


def test_queries_loaded_from_env_override(monkeypatch, tmp_path: Path) -> None:
    query_file = tmp_path / "queries.toml"
    query_file.write_text(
        """
[[queries]]
name = "q1"
terms = "enzyme engineering"
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("BAIODIGEST_QUERIES_FILE", str(query_file))

    settings = Settings()

    assert len(settings.pubmed_queries) == 1
    assert settings.pubmed_queries[0].name == "q1"


def test_queries_validation_failure_for_empty_list(monkeypatch, tmp_path: Path) -> None:
    query_file = tmp_path / "queries.toml"
    query_file.write_text("queries = []\n", encoding="utf-8")
    monkeypatch.setenv("BAIODIGEST_QUERIES_FILE", str(query_file))

    try:
        Settings()
        assert False, "Expected ValueError for empty queries"
    except ValueError as exc:
        assert "non-empty" in str(exc)
