from baiodigest.models import DailyDigest, DigestEntry, FilterResult, Paper, Summary


def test_daily_digest_json_round_trip() -> None:
    paper = Paper(
        title="Paper title",
        abstract="Paper abstract",
        authors=["Kim J"],
        affiliations=["Example Univ"],
        doi="10.1/abc",
        source="pubmed",
        source_type="published",
        journal="Nature",
        url="https://example.org/paper",
        category="bioinformatics",
        date="2026-03-01",
        mesh_terms=["Protein Engineering"],
        source_id="pmid-1",
    )
    result = FilterResult(
        relevant=True,
        confidence=0.91,
        category="protein_engineering",
        reason="Strong industry relevance",
        matched_keywords=["protein engineering", "enzyme"],
    )
    summary = Summary(
        background="배경",
        method="방법",
        result="결과",
        significance="의미",
    )
    digest = DailyDigest(
        date="2026-03-01",
        entries=[DigestEntry(paper=paper, filter_result=result, summary=summary)],
        stats={"collected": 10, "summarized": 1},
    )

    loaded = DailyDigest.from_json(digest.to_json())

    assert loaded.date == "2026-03-01"
    assert len(loaded.entries) == 1
    assert loaded.entries[0].paper.doi == "10.1/abc"
    assert loaded.entries[0].summary.result == "결과"


def test_daily_digest_json_round_trip_with_research_radar_fields() -> None:
    paper = Paper(
        title="Paper title",
        abstract="Paper abstract",
        authors=["Kim J"],
        affiliations=["Example Univ"],
        doi="10.1/abc",
        source="pubmed",
        source_type="published",
        journal="Nature",
        url="https://example.org/paper",
        category="bioinformatics",
        date="2026-03-01",
        mesh_terms=["Protein Engineering"],
        source_id="pmid-1",
    )
    result = FilterResult(
        relevant=True,
        confidence=0.91,
        category="protein_engineering",
        reason="산업적 활용 가치가 있다.",
        matched_keywords=["protein engineering", "enzyme"],
        topic_tags=["ai_protein_design", "enzyme_stability"],
        problem_tags=["stability", "screening_speed"],
        research_type="method",
        practical_distance="mid_term",
    )
    summary = Summary(
        background="배경",
        method="방법",
        result="결과",
        significance="의미",
        why_it_matters="효소 최적화 후보를 빠르게 판단할 수 있다.",
        novelty_note="기존 대비 적은 실험으로 설계했다.",
        application_note="산업용 효소 스크리닝에 참고 가능하다.",
        caution_note="실제 공정 조건 검증은 추가로 필요하다.",
    )
    digest = DailyDigest(
        date="2026-03-01",
        entries=[DigestEntry(paper=paper, filter_result=result, summary=summary)],
        stats={"collected": 10, "summarized": 1},
    )

    loaded = DailyDigest.from_json(digest.to_json())

    assert loaded.entries[0].summary.why_it_matters == "효소 최적화 후보를 빠르게 판단할 수 있다."
    assert loaded.entries[0].summary.application_note == "산업용 효소 스크리닝에 참고 가능하다."
    assert loaded.entries[0].filter_result.topic_tags == ["ai_protein_design", "enzyme_stability"]
    assert loaded.entries[0].filter_result.problem_tags == ["stability", "screening_speed"]
    assert loaded.entries[0].filter_result.research_type == "method"
    assert loaded.entries[0].filter_result.practical_distance == "mid_term"
