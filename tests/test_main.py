from datetime import date

from baiodigest import main as main_module
from baiodigest.models import FilterResult, Paper, Summary


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


def test_run_pipeline_writes_research_radar_fields(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("BAIODIGEST_DATA_DIR", str(tmp_path))

    paper = Paper(
        title="Protein engineering with AI",
        abstract="Test abstract",
        authors=["A"],
        affiliations=["Example Institute"],
        doi=None,
        source="pubmed",
        source_type="published",
        journal="Test Journal",
        url="https://example.org",
        category=None,
        date="2026-03-07",
        mesh_terms=[],
    )
    filter_result = FilterResult(
        relevant=True,
        confidence=0.85,
        category="ai_enzyme",
        reason="산업적 활용 가능성이 있어 관련 논문으로 판단했습니다.",
        topic_tags=["ai_protein_design"],
        problem_tags=["stability"],
        research_type="method",
        practical_distance="mid_term",
    )
    summary = Summary(
        background="배경",
        method="방법",
        result="결과",
        significance="의미",
        why_it_matters="읽을 가치가 있다.",
        novelty_note="새 접근이다.",
        application_note="실무 적용 가능성이 있다.",
        caution_note="추가 검증이 필요하다.",
    )

    class _FakeOllamaClient:
        def __init__(self, settings) -> None:
            self.settings = settings

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def summarize(self, title: str, abstract: str) -> Summary:
            return summary

    monkeypatch.setattr(main_module, "_fetch_papers", lambda target, settings: ([paper], date(2026, 3, 7)))
    monkeypatch.setattr(main_module, "filter_papers", lambda papers, settings, ollama: ([(paper, filter_result)], 1))
    monkeypatch.setattr(main_module, "OllamaClient", _FakeOllamaClient)

    processed = main_module._run_pipeline_for_date(date(2026, 3, 8), force=False, fetch_only=False)

    assert processed is True
    digest = main_module.DailyDigest.from_file(tmp_path / "2026-03-08.json")
    assert digest.entries[0].summary.why_it_matters == "읽을 가치가 있다."
    assert digest.entries[0].filter_result.topic_tags == ["ai_protein_design"]
    assert digest.entries[0].filter_result.practical_distance == "mid_term"
