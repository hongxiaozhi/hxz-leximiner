from __future__ import annotations

import re
from collections import Counter
from typing import Dict, Iterable, List, Sequence, Set

from nltk.corpus import stopwords

from core.lemmatizer import Lemmatizer
from core.nltk_resources import ensure_nltk_resources, has_nltk_resource
from core.schemas import WordResult


TOKEN_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")

DEFAULT_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was", "were",
    "will", "with", "about", "after", "before", "between", "but", "into", "than", "then",
    "their", "there", "these", "those", "through", "very", "can", "could", "should",
    "would", "may", "might", "do", "does", "did", "not", "such", "if", "while", "during",
}


class WordExtractor:
    """Extract clean English words, lemmas, and frequencies."""

    def __init__(self, extra_stopwords: Iterable[str] | None = None) -> None:
        ensure_nltk_resources()
        self.lemmatizer = Lemmatizer()
        if has_nltk_resource("corpora/stopwords"):
            self.stopwords = set(stopwords.words("english"))
        else:
            self.stopwords = set(DEFAULT_STOPWORDS)
        if extra_stopwords:
            self.stopwords.update(word.lower() for word in extra_stopwords)

    def tokenize(self, text: str) -> List[str]:
        return [token.lower() for token in TOKEN_PATTERN.findall(text)]

    def filter_tokens(self, tokens: Sequence[str], remove_stopwords: bool = False) -> List[str]:
        filtered: List[str] = []
        for token in tokens:
            if len(token) <= 1:
                continue
            if remove_stopwords and token in self.stopwords:
                continue
            filtered.append(token)
        return filtered

    def extract_word_details(self, text: str, sentences: Sequence[str]) -> Dict[str, Dict[str, str | int]]:
        tokens = self.filter_tokens(self.tokenize(text), remove_stopwords=False)
        lemmas = self.lemmatizer.lemmatize_tokens(tokens)
        lemma_counter = Counter(lemmas)
        source_sentence_map = self._build_source_sentence_map(sentences)

        word_details: Dict[str, Dict[str, str | int]] = {}
        for token, lemma in zip(tokens, lemmas):
            if lemma not in word_details:
                word_details[lemma] = {
                    "word": token,
                    "lemma": lemma,
                    "frequency": lemma_counter[lemma],
                    "source_sentence": source_sentence_map.get(lemma, ""),
                }
        return word_details

    def build_word_results(self, text: str, sentences: Sequence[str]) -> List[WordResult]:
        word_details = self.extract_word_details(text, sentences)
        sorted_items = sorted(word_details.values(), key=lambda item: (-int(item["frequency"]), str(item["lemma"])))
        return [
            WordResult(
                word=str(item["word"]),
                lemma=str(item["lemma"]),
                frequency=int(item["frequency"]),
                category="unknown",
                level="unknown",
                frequency_band="unknown",
                chinese_meaning="",
                phonetic="",
                mnemonic="",
                source_sentence=str(item["source_sentence"]),
                remark="",
            )
            for item in sorted_items
        ]

    def _build_source_sentence_map(self, sentences: Sequence[str]) -> Dict[str, str]:
        source_map: Dict[str, str] = {}
        for sentence in sentences:
            tokens = self.filter_tokens(self.tokenize(sentence), remove_stopwords=False)
            if not tokens:
                continue
            lemmas = self.lemmatizer.lemmatize_tokens(tokens)
            for lemma in lemmas:
                source_map.setdefault(lemma, sentence)
        return source_map


if __name__ == "__main__":
    sample_text = (
        "LexiMiner extracts important words from English texts. "
        "It also tracks repeated words and basic phrases."
    )
    extractor = WordExtractor()
    sentences = [
        "LexiMiner extracts important words from English texts.",
        "It also tracks repeated words and basic phrases.",
    ]
    results = extractor.build_word_results(sample_text, sentences)
    for item in results[:10]:
        print(item.to_dict())