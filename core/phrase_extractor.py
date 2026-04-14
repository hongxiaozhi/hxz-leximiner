from __future__ import annotations

from collections import Counter
from typing import Iterable, List, Sequence

from core.schemas import PhraseResult


class PhraseExtractor:
    """Extract simple bigram and trigram phrases from tokens."""

    def __init__(self, stopwords: Iterable[str]) -> None:
        self.stopwords = {word.lower() for word in stopwords}

    def extract_phrases(
        self,
        tokens: Sequence[str],
        sentences: Sequence[str] | None = None,
        min_frequency: int = 1,
        phrase_meanings: dict[str, str] | None = None,
        word_meanings: dict[str, str] | None = None,
    ) -> List[PhraseResult]:
        normalized = [token.lower() for token in tokens if token.isalpha() and len(token) > 1]
        candidates = self._generate_ngrams(normalized, 2) + self._generate_ngrams(normalized, 3)
        counter = Counter(candidates)

        phrase_results: List[PhraseResult] = []
        for phrase, frequency in counter.items():
            if frequency < min_frequency:
                continue
            if self._is_invalid_phrase(phrase):
                continue
            phrase_results.append(
                PhraseResult(
                    phrase=phrase,
                    frequency=frequency,
                    category="ngram",
                    chinese_meaning=self._build_phrase_meaning(phrase, phrase_meanings or {}, word_meanings or {}),
                    source_sentence=self._find_sentence(phrase, sentences or []),
                )
            )

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

    def _build_phrase_meaning(
        self,
        phrase: str,
        phrase_meanings: dict[str, str],
        word_meanings: dict[str, str],
    ) -> str:
        exact_meaning = phrase_meanings.get(phrase)
        if exact_meaning:
            return exact_meaning

        parts = [part for part in phrase.split() if part]
        if not parts:
            return "短语释义"

        composed_parts: list[str] = []
        for part in parts:
            if part in word_meanings:
                composed_parts.append(word_meanings[part])
        if composed_parts:
            return " + ".join(composed_parts)

        return f"短语释义：{'，'.join(parts)}"

    def _find_sentence(self, phrase: str, sentences: Sequence[str]) -> str:
        for sentence in sentences:
            if phrase in sentence.lower():
                return sentence
        return ""