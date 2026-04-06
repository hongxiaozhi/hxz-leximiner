from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import nltk
from nltk.stem import WordNetLemmatizer

try:
    from core.nltk_resources import ensure_nltk_resources, has_nltk_resource
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from core.nltk_resources import ensure_nltk_resources, has_nltk_resource


class Lemmatizer:
    """Lemmatize English tokens with a light POS-aware strategy."""

    def __init__(self) -> None:
        ensure_nltk_resources()
        self._lemmatizer = WordNetLemmatizer()
        self._has_wordnet = has_nltk_resource("corpora/wordnet")
        self._has_tagger = has_nltk_resource("taggers/averaged_perceptron_tagger_eng")

    @staticmethod
    def _to_wordnet_pos(treebank_tag: str) -> str:
        if treebank_tag.startswith("J"):
            return "a"
        if treebank_tag.startswith("V"):
            return "v"
        if treebank_tag.startswith("R"):
            return "r"
        return "n"

    def lemmatize_tokens(self, tokens: Sequence[str]) -> List[str]:
        lemmas: List[str] = []

        if self._has_wordnet and self._has_tagger:
            tagged_tokens: Iterable[Tuple[str, str]] = nltk.pos_tag(list(tokens))
            for token, pos_tag in tagged_tokens:
                lemma = self._lemmatizer.lemmatize(token, self._to_wordnet_pos(pos_tag))
                lemmas.append(lemma.lower())
            return lemmas

        for token in tokens:
            lemmas.append(self._simple_lemmatize(token))
        return lemmas

    def _simple_lemmatize(self, token: str) -> str:
        lower = token.lower()
        if lower.endswith("ies") and len(lower) > 4:
            return lower[:-3] + "y"
        if lower.endswith("ing") and len(lower) > 5:
            return lower[:-3]
        if lower.endswith("ed") and len(lower) > 4:
            return lower[:-2]
        if lower.endswith("es") and len(lower) > 4:
            return lower[:-2]
        if lower.endswith("s") and len(lower) > 3:
            return lower[:-1]
        return lower