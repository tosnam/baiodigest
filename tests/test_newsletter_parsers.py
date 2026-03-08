from pathlib import Path

from baiodigest.newsletters.parsers import parse_nature_issue, parse_science_issue


def test_parse_nature_issue_extracts_multiple_main_items() -> None:
    html = Path("tests/fixtures/nature_newsletter.html").read_text(encoding="utf-8")

    issue = parse_nature_issue(message_id="m1", thread_id="t1", subject="Nature Briefing", html=html)

    assert issue.source == "nature"
    assert len(issue.sections) >= 1
    assert sum(len(section.items) for section in issue.sections) >= 3


def test_parse_science_issue_extracts_multiple_main_items() -> None:
    html = Path("tests/fixtures/science_newsletter.html").read_text(encoding="utf-8")

    issue = parse_science_issue(message_id="m2", thread_id="t2", subject="Science", html=html)

    assert issue.source == "science"
    assert sum(len(section.items) for section in issue.sections) >= 3


def test_parse_nature_issue_falls_back_to_meaningful_anchor_texts() -> None:
    html = """
    <html>
      <body>
        <table>
          <tr><td><a href="https://example.com/browser">View this email in your browser</a></td></tr>
          <tr><td><a href="https://example.com/story-a">How these koalas came back from the brink</a></td></tr>
          <tr><td><a href="https://example.com/story-b">Protein-clearing cells break in Alzheimer’s</a></td></tr>
          <tr><td><a href="https://example.com/story-c">A Möbius molecule with a new twist</a></td></tr>
        </table>
      </body>
    </html>
    """

    issue = parse_nature_issue(message_id="m3", thread_id="t3", subject="Nature Briefing", html=html)

    titles = [item.title for section in issue.sections for item in section.items]
    assert "View this email in your browser" not in titles
    assert "How these koalas came back from the brink" in titles
    assert len(titles) >= 3


def test_parse_science_issue_extracts_story_cards_from_email_tables() -> None:
    html = """
    <html>
      <body>
        <table>
          <tr>
            <td style="font: 600 22px/28px Roboto,Arial,sans-serif;">
              <a href="https://example.com/story-a">An alleged nuclear blast may reignite weapons testing, and who owns the Moon</a>
            </td>
          </tr>
          <tr>
            <td style="font: 400 14px/20px Roboto,Arial,sans-serif; color:#595959;">
              By Example Author | 5 March 2025
            </td>
          </tr>
          <tr>
            <td style="font: 600 22px/28px Roboto,Arial,sans-serif;">
              <a href="https://example.com/story-b">Why cats always land on their feet</a>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """

    issue = parse_science_issue(message_id="m4", thread_id="t4", subject="Science", html=html)

    titles = [item.title for section in issue.sections for item in section.items]
    assert "An alleged nuclear blast may reignite weapons testing, and who owns the Moon" in titles
    assert "Why cats always land on their feet" in titles


def test_parse_science_issue_uses_first_meaningful_link_per_story_paragraph() -> None:
    html = """
    <html>
      <body>
        <td style="font: 400 18px/27px 'PT Serif',Georgia,'Times New Roman',Times,serif;">
          Heart attacks are common, and researchers suggest
          <a href="https://example.com/story-a">a single shot in the arm</a>.
          Follow-up data showed
          <a href="https://example.com/story-a-detail">saRNA boosted ANP levels and reduced heart inflammation for 4 weeks</a>.
        </td>
        <td style="font: 400 18px/27px 'PT Serif',Georgia,'Times New Roman',Times,serif;">
          Evolutionary biologists found
          <a href="https://example.com/story-b">peptides extraordinarily similar to bradykinin arose over and over again in both groups</a>.
          One author said
          <a href="https://example.com/story-b-quote">They are evolutionary doppelgängers</a>.
        </td>
      </body>
    </html>
    """

    issue = parse_science_issue(message_id="m6", thread_id="t6", subject="Science", html=html)

    titles = [item.title for section in issue.sections for item in section.items]
    assert titles == [
        "a single shot in the arm",
        "peptides extraordinarily similar to bradykinin arose over and over again in both groups",
    ]


def test_parse_science_issue_matches_body_blocks_without_explicit_font_weight() -> None:
    html = """
    <html>
      <body>
        <td style="font: 18px/27px 'PT Serif',Georgia,'Times New Roman',Times,serif; color:#262626;">
          Anyone who's ever watched a cat twist midair knows
          <a href="https://example.com/story-c">that those bendy backs are what let them always land on their feet</a>.
          A related explainer noted
          <a href="https://example.com/story-c-detail">cats use their tails to control rotation</a>.
        </td>
      </body>
    </html>
    """

    issue = parse_science_issue(message_id="m7", thread_id="t7", subject="Science", html=html)
    titles = [item.title for section in issue.sections for item in section.items]

    assert titles == ["that those bendy backs are what let them always land on their feet"]


def test_parse_science_issue_matches_pt_serif_16px_body_blocks() -> None:
    html = """
    <html>
      <body>
        <td style="font: 16px/24px 'PT Serif',Georgia,'Times New Roman',Times,serif; color:#595959; padding-top:15px;">
          Researchers discovered
          <a href="https://example.com/story-d">peptides extraordinarily similar to bradykinin arose over and over again in both groups</a>.
          One scientist said
          <a href="https://example.com/story-d-quote">They are evolutionary doppelgängers</a>.
        </td>
      </body>
    </html>
    """

    issue = parse_science_issue(message_id="m8", thread_id="t8", subject="Science", html=html)
    titles = [item.title for section in issue.sections for item in section.items]

    assert titles == ["peptides extraordinarily similar to bradykinin arose over and over again in both groups"]


def test_parse_nature_issue_prefers_h2_article_titles_over_nested_inline_links() -> None:
    html = """
    <html>
      <body>
        <tr>
          <td class="content-block">
            <h2><a href="https://example.com/story-a">How these koalas came back from the brink</a></h2>
            <p>
              Researchers found that the number of individuals has
              <a href="https://example.com/snippet-a">jumped substantially in the past few decades</a>.
            </p>
            <span class="content-reference"><a href="https://example.com/reference-a">Nature | 4 min read</a></span>
          </td>
        </tr>
      </body>
    </html>
    """

    issue = parse_nature_issue(message_id="m5", thread_id="t5", subject="Nature Briefing", html=html)

    titles = [item.title for section in issue.sections for item in section.items]
    assert titles == ["How these koalas came back from the brink"]


def test_parse_issue_text_body_ignores_style_block_noise() -> None:
    html = """
    <html>
      <head>
        <style>
          body { font-size: 14px; }
          .hero { color: red; }
        </style>
      </head>
      <body>
        <h1>Nature Briefing</h1>
        <p>Main story text only.</p>
      </body>
    </html>
    """

    issue = parse_nature_issue(message_id="m9", thread_id="t9", subject="Nature Briefing", html=html)

    assert "font-size" not in issue.text_body
    assert "Main story text only." in issue.text_body
