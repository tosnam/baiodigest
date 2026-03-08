from baiodigest.newsletters.gmail_client import extract_html_body, get_message, list_labeled_message_ids
from baiodigest.newsletters.fetch import fetch_newsletters, save_issue
from baiodigest.newsletters.parsers import parse_nature_issue, parse_science_issue
from baiodigest.newsletters.state import NewsletterCheckpoint, load_checkpoint, save_checkpoint

__all__ = [
    "NewsletterCheckpoint",
    "extract_html_body",
    "fetch_newsletters",
    "get_message",
    "list_labeled_message_ids",
    "load_checkpoint",
    "parse_nature_issue",
    "parse_science_issue",
    "save_issue",
    "save_checkpoint",
]
