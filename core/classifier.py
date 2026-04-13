from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Set


class VocabularyClassifier:
    """Classify words and phrases with local vocabulary lists."""

    WORD_PRIORITY = ("academic", "ielts", "cet6", "cet4", "high_school")
    LEVEL_ORDER = {
        "high_school": 1,
        "cet4": 2,
        "cet6": 3,
        "ielts": 4,
        "academic": 5,
    }

    def __init__(self, vocab_dir: Path) -> None:
        self.vocab_dir = vocab_dir
        self.vocab_map = self._load_vocabularies()
        self.phrase_dict = self._load_word_list(vocab_dir / "phrase_dict.txt")
        self.phrase_meanings = self._load_phrase_meanings(vocab_dir / "phrase_meanings.json")

    def classify_word(self, lemma: str) -> str:
        normalized = lemma.lower().strip()
        for category in self.WORD_PRIORITY:
            if normalized in self.vocab_map[category]:
                return category
        return self._heuristic_level(normalized)

    def estimate_frequency_band(self, lemma: str, frequency: int) -> str:
        if frequency >= 5:
            return "high_frequency"
        if frequency >= 2:
            return "mid_frequency"
        normalized = lemma.lower().strip()
        if normalized in self.vocab_map["academic"]:
            return "academic_low_frequency"
        return "low_frequency"

    def classify_phrase(self, phrase: str) -> str:
        normalized = phrase.lower().strip()
        if normalized in self.phrase_dict:
            return "phrase_dict"
        return "ngram"

    def get_phrase_meaning(self, phrase: str) -> str:
        normalized = phrase.lower().strip()
        return self.phrase_meanings.get(normalized, f"常用短语：{phrase}")

    def _load_vocabularies(self) -> Dict[str, Set[str]]:
        return {
            "academic": self._load_word_list(self.vocab_dir / "academic.txt"),
            "ielts": self._load_word_list(self.vocab_dir / "ielts.txt"),
            "cet6": self._load_word_list(self.vocab_dir / "cet6.txt"),
            "cet4": self._load_word_list(self.vocab_dir / "cet4.txt"),
            "high_school": self._load_word_list(self.vocab_dir / "high_school.txt"),
        }

    def _heuristic_level(self, lemma: str) -> str:
        if len(lemma) <= 4:
            return "high_school"
        if len(lemma) <= 6:
            return "cet4"
        if len(lemma) <= 8:
            return "cet6"
        return "ielts"

    def _load_word_list(self, file_path: Path) -> Set[str]:
        if not file_path.exists():
            return set()

        items: Set[str] = set()
        for line in file_path.read_text(encoding="utf-8").splitlines():
            word = line.strip().lower()
            if not word or word.startswith("#"):
                continue
            items.add(word)
        return items

    def _load_phrase_meanings(self, file_path: Path) -> Dict[str, str]:
        if not file_path.exists():
            return {}
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return {str(key).lower().strip(): str(value) for key, value in data.items() if str(key).strip()}