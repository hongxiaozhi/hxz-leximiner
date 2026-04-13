from __future__ import annotations

from pathlib import Path

from core.classifier import VocabularyClassifier
from core.metadata import WordMetadataService
from core.phrase_extractor import PhraseExtractor
from core.preprocess import clean_text, split_sentences
from core.schemas import AnalysisResult, AnalysisSummary
from core.word_extractor import WordExtractor


class LexiMinerAnalyzer:
    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path(__file__).resolve().parents[1]
        self.vocab_dir = self.project_root / "data" / "vocab"
        self.word_extractor = WordExtractor()
        self.classifier = VocabularyClassifier(vocab_dir=self.vocab_dir)
        self.phrase_extractor = PhraseExtractor(stopwords=self.word_extractor.stopwords)
        self.word_metadata_service = WordMetadataService(vocab_dir=self.vocab_dir)

    def analyze_text(self, text: str, use_online_translation: bool = False) -> AnalysisResult:
        cleaned_text = clean_text(text)
        sentences = split_sentences(cleaned_text)
        word_results = self.word_extractor.build_word_results(cleaned_text, sentences)
        for item in word_results:
            item.category = self.classifier.classify_word(item.lemma)
        self.word_metadata_service.enrich_words(word_results, use_online_translation=use_online_translation)
        tokens_for_phrases = self.word_extractor.filter_tokens(self.word_extractor.tokenize(cleaned_text), remove_stopwords=True)
        phrase_results = self.phrase_extractor.extract_phrases(tokens=tokens_for_phrases)
        for item in phrase_results:
            item.category = self.classifier.classify_phrase(item.phrase)
        summary = AnalysisSummary(
            total_words=sum(item.frequency for item in word_results),
            unique_words=len(word_results),
            total_phrases=len(phrase_results),
            total_sentences=len(sentences),
        )
        return AnalysisResult(words=word_results, phrases=phrase_results, summary=summary)