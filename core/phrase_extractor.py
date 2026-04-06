from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Sequence

try:
    from models.schemas import PhraseResult
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from models.schemas import PhraseResult


class PhraseExtractor:
    """Extract simple bigram and trigram phrases from tokens."""

    def __init__(self, stopwords: Iterable[str]) -> None:
        self.stopwords = {word.lower() for word in stopwords}

    def extract_phrases(self, tokens: Sequence[str], min_frequency: int = 1) -> List[PhraseResult]:
        normalized = [token.lower() for token in tokens if token.isalpha() and len(token) > 1]
        candidates = self._generate_ngrams(normalized, 2) + self._generate_ngrams(normalized, 3)
        counter = Counter(candidates)

        phrase_results: List[PhraseResult] = []
        for phrase, frequency in counter.items():
            if frequency < min_frequency:
                continue
            if self._is_invalid_phrase(phrase):
                continue
            phrase_results.append(PhraseResult(phrase=phrase, frequency=frequency, category="ngram"))

        phrase_results.sort(key=lambda item: (-item.frequency, item.phrase))
        return phrase_results

    def _generate_ngrams(self, tokens: Sequence[str], n: int) -> List[str]:
        if len(tokens) < n:
            return []
        return [" ".join(tokens[index:index + n]) for index in range(len(tokens) - n + 1)]

    def _is_invalid_phrase(self, phrase: str) -> bool:
        parts = phrase.split()
        if all(part in self.stopwords for part in parts):
            return True
        if any(not part.isalpha() for part in parts):
            return True
        return False