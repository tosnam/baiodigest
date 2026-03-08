from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(slots=True)
class NewsletterCheckpoint:
    last_internal_date_ms: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def load_checkpoint(path: Path) -> NewsletterCheckpoint:
    if not path.exists():
        return NewsletterCheckpoint()

    data = json.loads(path.read_text(encoding="utf-8"))
    return NewsletterCheckpoint(last_internal_date_ms=int(data.get("last_internal_date_ms", 0)))


def save_checkpoint(path: Path, checkpoint: NewsletterCheckpoint) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(checkpoint.to_dict(), indent=2), encoding="utf-8")
