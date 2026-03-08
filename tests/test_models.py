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


def test_daily_digest_json_round_trip_after_radar_reset() -> None:
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
    )
    summary = Summary(background="배경", method="방법", result="결과", significance="의미")
    digest = DailyDigest(
        date="2026-03-01",
        entries=[DigestEntry(paper=paper, filter_result=result, summary=summary)],
        stats={"collected": 10, "summarized": 1},
    )

    loaded = DailyDigest.from_json(digest.to_json())

    assert loaded.entries[0].summary.significance == "의미"
    assert not hasattr(loaded.entries[0].summary, "why_it_matters")
    assert not hasattr(loaded.entries[0].filter_result, "topic_tags")


def test_daily_digest_json_round_trip_without_optional_summary_notes() -> None:
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

    assert loaded.entries[0].summary.significance == "의미"
    assert not hasattr(loaded.entries[0].summary, "application_note")
    assert not hasattr(loaded.entries[0].summary, "caution_note")
