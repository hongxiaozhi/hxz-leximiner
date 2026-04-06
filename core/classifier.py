from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Set


class VocabularyClassifier:
    """Classify words and phrases with local vocabulary lists."""

    PRIORITY = ("academic", "cet6", "cet4")

    def __init__(self, vocab_dir: Path) -> None:
        self.vocab_dir = vocab_dir
        self.vocab_map = self._load_vocabularies()
        self.phrase_dict = self._load_word_list(vocab_dir / "phrase_dict.txt")

    def classify_word(self, lemma: str) -> str:
        normalized = lemma.lower().strip()
        for category in self.PRIORITY:
            if normalized in self.vocab_map[category]:
                return category
        return "unknown"

    def classify_phrase(self, phrase: str) -> str:
        normalized = phrase.lower().strip()
        if normalized in self.phrase_dict:
            return "phrase_dict"
        return "ngram"

    def _load_vocabularies(self) -> Dict[str, Set[str]]:
        return {
            "academic": self._load_word_list(self.vocab_dir / "academic.txt"),
            "cet6": self._load_word_list(self.vocab_dir / "cet6.txt"),
            "cet4": self._load_word_list(self.vocab_dir / "cet4.txt"),
        }

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