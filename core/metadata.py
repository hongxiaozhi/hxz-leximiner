from __future__ import annotations

import json
import re
from pathlib import Path

import eng_to_ipa as ipa

try:
    from deep_translator import GoogleTranslator
except ModuleNotFoundError:
    GoogleTranslator = None


class WordMetadataService:
    MORPHEME_HINTS = {
        "re": "re 表示 again，再、重新",
        "un": "un 表示 not，否定含义",
        "dis": "dis 表示 not/away，否定或分离",
        "pre": "pre 表示 before，在前",
        "pro": "pro 表示 forward，向前",
        "sub": "sub 表示 under，在下",
        "trans": "trans 表示 across，跨越",
        "inter": "inter 表示 between，之间",
        "tion": "-tion 常构成名词，表示行为或结果",
        "sion": "-sion 常构成名词，表示过程或状态",
        "ment": "-ment 常构成名词，表示结果或状态",
        "able": "-able 表示 can be，可以被",
        "ing": "-ing 常表示进行或动作过程",
        "ed": "-ed 常表示过去或完成",
        "ly": "-ly 常构成副词，表示方式",
    }

    def __init__(self, vocab_dir: Path) -> None:
        self.vocab_dir = vocab_dir
        self.local_dictionary_path = self.vocab_dir / "local_dictionary.json"
        self.override_path = self.vocab_dir / "word_metadata.json"
        self.local_dictionary = self._load_json(self.local_dictionary_path)
        self.overrides = self._load_json(self.override_path)
        self.translator = None

    def enable_online_translation(self) -> None:
        if self.translator is None and GoogleTranslator is not None:
            self.translator = GoogleTranslator(source="en", target="zh-CN")

    def enrich_words(self, words, use_online_translation: bool = False) -> None:
        if use_online_translation:
            self.enable_online_translation()

        for item in words:
            metadata = self.get_metadata(item.lemma, use_online_translation=use_online_translation)
            item.chinese_meaning = metadata.chinese_meaning
            item.phonetic = metadata.phonetic
            item.mnemonic = metadata.mnemonic

    def get_metadata(self, lemma: str, use_online_translation: bool = False):
        normalized = lemma.lower().strip()
        if normalized in self.local_dictionary:
            return self._pack_metadata(normalized, self.local_dictionary[normalized])
        if normalized in self.overrides:
            return self._pack_metadata(normalized, self.overrides[normalized])
        metadata = {
            "chinese_meaning": self._translate_to_chinese(normalized, use_online_translation),
            "phonetic": self._build_phonetic(normalized),
            "mnemonic": self._build_mnemonic(normalized),
        }
        return self._pack_metadata(normalized, metadata, sync=False)

    def _pack_metadata(self, word: str, data, sync: bool = True):
        metadata = type("WordMetadata", (), {})()
        metadata.chinese_meaning = data.get("chinese_meaning", "")
        metadata.phonetic = data.get("phonetic", "")
        metadata.mnemonic = data.get("mnemonic", "")
        return metadata

    def _translate_to_chinese(self, word: str, use_online_translation: bool = False) -> str:
        if use_online_translation and self.translator is not None:
            try:
                translated = self.translator.translate(word)
                if translated and translated.lower() != word.lower():
                    return translated
            except Exception:
                pass
        return f"{word}（建议后续补充本地词典释义）"

    def _build_phonetic(self, word: str) -> str:
        try:
            phonetic = ipa.convert(word).strip()
            if phonetic and phonetic != word:
                return f"/{phonetic}/"
        except Exception:
            pass
        return f"/{word}/"

    def _build_mnemonic(self, word: str) -> str:
        matched_hints = [hint for part, hint in self.MORPHEME_HINTS.items() if word.startswith(part) or word.endswith(part)]
        if matched_hints:
            return "；".join(matched_hints[:2])
        chunks = [chunk for chunk in re.split(r"([aeiouy]+)", word) if chunk]
        if len(chunks) >= 2:
            preview = "-".join(chunks[:3])
            return f"可按发音片段记忆：{preview}"
        return f"可结合词形 {word} 反复朗读记忆"

    @staticmethod
    def _load_json(file_path: Path):
        if not file_path.exists():
            return {}
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}