from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_EXTENSIONS = {".md", ".txt", ".json", ".csv", ".yaml", ".yml"}


@dataclass(frozen=True)
class KnowledgeHit:
    path: str
    line: int
    score: int
    preview: str


class LocalKnowledgeBase:
    def __init__(self, root: Path | str, max_file_bytes: int = 300_000):
        self.root = Path(root)
        self.max_file_bytes = max_file_bytes

    def search(self, query: str, limit: int = 5) -> list[KnowledgeHit]:
        terms = self._terms(query)
        if not terms or not self.root.exists():
            return []

        hits: list[KnowledgeHit] = []
        for path in self._iter_files():
            try:
                if path.stat().st_size > self.max_file_bytes:
                    continue
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue

            for line_number, line in enumerate(lines, start=1):
                score = self._score(line, terms)
                if score <= 0:
                    continue
                hits.append(
                    KnowledgeHit(
                        path=path.relative_to(self.root).as_posix(),
                        line=line_number,
                        score=score,
                        preview=line.strip()[:240],
                    )
                )

        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]

    def _iter_files(self) -> list[Path]:
        return [
            path
            for path in self.root.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

    @staticmethod
    def _terms(query: str) -> list[str]:
        return [term.lower() for term in re.findall(r"[a-zA-Z0-9_-]+", query)]

    @staticmethod
    def _score(line: str, terms: list[str]) -> int:
        normalized = line.lower()
        score = 0
        for term in terms:
            occurrences = normalized.count(term)
            if occurrences:
                score += occurrences
                if re.search(rf"\b{re.escape(term)}\b", normalized):
                    score += 2
        return score
