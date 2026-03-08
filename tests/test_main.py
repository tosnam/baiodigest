from datetime import date

from baiodigest import main as main_module
from baiodigest.config import Settings


class _FixedDate(date):
    @classmethod
    def today(cls) -> "_FixedDate":
        return cls(2026, 3, 3)


def test_target_dates_defaults_to_today_digest_date(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(main_module, "date", _FixedDate)

    targets = main_module._target_dates(tmp_path, explicit_date=None, max_backfill_days=5)

    assert targets == [date(2026, 3, 3)]


def test_target_dates_skips_when_today_digest_already_collected(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(main_module, "date", _FixedDate)
    (tmp_path / "2026-03-03.json").write_text("{}", encoding="utf-8")

    targets = main_module._target_dates(tmp_path, explicit_date=None, max_backfill_days=5)

    assert targets == []


def test_target_dates_backfills_until_today_with_limit(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(main_module, "date", _FixedDate)
    (tmp_path / "2026-02-25.json").write_text("{}", encoding="utf-8")

    targets = main_module._target_dates(tmp_path, explicit_date=None, max_backfill_days=3)

    assert targets == [
        date(2026, 3, 1),
        date(2026, 3, 2),
        date(2026, 3, 3),
    ]


def test_pubmed_query_date_is_previous_day() -> None:
    assert main_module._pubmed_query_date(date(2026, 3, 4)) == date(2026, 3, 3)
    assert main_module._pubmed_query_date(date(2026, 1, 1)) == date(2025, 12, 31)


def test_site_prefix_keeps_project_prefix_for_docs_output(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("BAIODIGEST_ROOT", str(tmp_path))
    (tmp_path / "queries.toml").write_text('[[queries]]\nname = "q"\nterms = "t"\n', encoding="utf-8")

    settings = Settings()
    settings.docs_dir = tmp_path / "docs"

    assert main_module._site_prefix_for_output(settings) == "/baiodigest"


def test_site_prefix_uses_root_prefix_for_preview_output(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("BAIODIGEST_ROOT", str(tmp_path))
    (tmp_path / "queries.toml").write_text('[[queries]]\nname = "q"\nterms = "t"\n', encoding="utf-8")

    settings = Settings()
    settings.docs_dir = tmp_path / "preview"

    assert main_module._site_prefix_for_output(settings) == ""
