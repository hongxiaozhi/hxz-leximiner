from __future__ import annotations

import sys
from pathlib import Path

try:
    from core.classifier import VocabularyClassifier
    from core.phrase_extractor import PhraseExtractor
    from core.preprocess import clean_text, split_sentences
    from core.word_extractor import WordExtractor
    from models.schemas import AnalysisResult, AnalysisSummary
    from services.word_metadata_service import WordMetadataService
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from core.classifier import VocabularyClassifier
    from core.phrase_extractor import PhraseExtractor
    from core.preprocess import clean_text, split_sentences
    from core.word_extractor import WordExtractor
    from models.schemas import AnalysisResult, AnalysisSummary
    from services.word_metadata_service import WordMetadataService


class AnalysisService:
    """Coordinate the full text analysis pipeline."""

    def __init__(self, vocab_dir: Path, output_dir: Path) -> None:
        self.vocab_dir = vocab_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.word_extractor = WordExtractor()
        self.classifier = VocabularyClassifier(vocab_dir=vocab_dir)
        self.phrase_extractor = PhraseExtractor(stopwords=self.word_extractor.stopwords)
        self.word_metadata_service = WordMetadataService(vocab_dir=vocab_dir, output_dir=output_dir)

    def analyze_text(self, text: str, use_online_translation: bool = False) -> AnalysisResult:
        cleaned_text = clean_text(text)
        sentences = split_sentences(cleaned_text)

        word_results = self.word_extractor.build_word_results(cleaned_text, sentences)
        for item in word_results:
            item.category = self.classifier.classify_word(item.lemma)
        self.word_metadata_service.enrich_words(
            word_results,
            use_online_translation=use_online_translation,
        )

        tokens_for_phrases = self.word_extractor.filter_tokens(
            self.word_extractor.tokenize(cleaned_text),
            remove_stopwords=True,
        )
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