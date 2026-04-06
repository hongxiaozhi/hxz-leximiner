from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List


@dataclass(slots=True)
class WordResult:
    word: str
    lemma: str
    frequency: int
    category: str
    chinese_meaning: str = ""
    phonetic: str = ""
    mnemonic: str = ""
    source_sentence: str = ""
    remark: str = ""

    def to_dict(self) -> Dict[str, str | int]:
        return asdict(self)


@dataclass(slots=True)
class PhraseResult:
    phrase: str
    frequency: int
    category: str

    def to_dict(self) -> Dict[str, str | int]:
        return asdict(self)


@dataclass(slots=True)
class AnalysisSummary:
    total_words: int
    unique_words: int
    total_phrases: int
    total_sentences: int


@dataclass(slots=True)
class AnalysisResult:
    words: List[WordResult]
    phrases: List[PhraseResult]
    summary: AnalysisSummary