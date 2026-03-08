from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import re

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from baiodigest.config import Settings
from baiodigest.models import Summary
from baiodigest.summarizer.prompts import build_relevance_prompt, build_summary_prompt

logger = logging.getLogger(__name__)


class OllamaResponseError(RuntimeError):
    pass


@dataclass(slots=True)
class RelevanceDecision:
    relevant: bool
    confidence: float
    category: str
    reason: str
    topic_tags: list[str]
    problem_tags: list[str]
    research_type: str
    practical_distance: str


def _extract_json_block(text: str) -> dict:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if not match:
        raise OllamaResponseError("No JSON object found in Ollama response")

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise OllamaResponseError("Failed to parse JSON block") from exc


def _split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]


def _fallback_summary(abstract: str) -> Summary:
    sentences = _split_sentences(abstract)
    s1 = sentences[0] if len(sentences) > 0 else "초록 기반 배경 정보를 추출하지 못했습니다."
    s2 = sentences[1] if len(sentences) > 1 else s1
    s3 = sentences[2] if len(sentences) > 2 else s2
    return Summary(
        background=s1,
        method=s2,
        result=s3,
        significance=s3,
    )


class OllamaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = httpx.Client(timeout=float(settings.ollama_timeout_sec))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
    def _generate(self, prompt: str) -> str:
        url = f"{self.settings.ollama_base_url}/api/generate"
        payload = {
            "model": self.settings.ollama_model,
            "prompt": "/no_think\n" + prompt,
            "stream": False,
        }
        resp = self.client.post(url, json=payload)
        resp.raise_for_status()

        data = resp.json()
        response_text = data.get("response", "")
        if not response_text:
            raise OllamaResponseError("Empty response from Ollama")
        return response_text

    def classify_relevance(self, title: str, abstract: str) -> RelevanceDecision:
        prompt = build_relevance_prompt(title, abstract)
        raw = self._generate(prompt)
        payload = _extract_json_block(raw)

        return RelevanceDecision(
            relevant=bool(payload.get("relevant", False)),
            confidence=float(payload.get("confidence", 0.0)),
            category=str(payload.get("category", "other")),
            reason=str(payload.get("reason", "")),
            topic_tags=[str(item).strip() for item in payload.get("topic_tags", []) if str(item).strip()],
            problem_tags=[str(item).strip() for item in payload.get("problem_tags", []) if str(item).strip()],
            research_type=str(payload.get("research_type", "")).strip(),
            practical_distance=str(payload.get("practical_distance", "")).strip(),
        )

    def summarize(self, title: str, abstract: str) -> Summary:
        prompt = build_summary_prompt(title, abstract)
        try:
            raw = self._generate(prompt)
            payload = _extract_json_block(raw)
            return Summary(
                background=str(payload.get("background", "")).strip(),
                method=str(payload.get("method", "")).strip(),
                result=str(payload.get("result", "")).strip(),
                significance=str(payload.get("significance", "")).strip(),
                why_it_matters=str(payload.get("why_it_matters", "")).strip(),
                novelty_note=str(payload.get("novelty_note", "")).strip(),
                application_note=str(payload.get("application_note", "")).strip(),
                caution_note=str(payload.get("caution_note", "")).strip(),
            )
        except Exception as exc:
            logger.warning("Summary generation failed, using fallback: %s", exc)
            return _fallback_summary(abstract)

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "OllamaClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
