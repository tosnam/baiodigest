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
