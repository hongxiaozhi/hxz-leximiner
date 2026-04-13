"""Merge downloaded vocabulary sources into LexiMiner local vocab files.

Expected input layout:
- data/vocab/source_files/core_frequency.txt
- data/vocab/source_files/dictionary_base.json
- data/vocab/source_files/cet4.txt
- data/vocab/source_files/cet6.txt
- data/vocab/source_files/ielts.txt
- data/vocab/source_files/toefl.txt

The script keeps the final structure compatible with:
- data/vocab/local_dictionary.json
- data/vocab/word_metadata.json
- data/vocab/phrase_meanings.json
"""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
VOCAB_DIR = ROOT / "data" / "vocab"
SOURCE_DIR = VOCAB_DIR / "source_files"


def read_word_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    words: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        words.append(line)
    return words


def read_json_dict(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return {str(key).strip().lower(): value for key, value in data.items() if str(key).strip()}
    return {}


def normalize_word(word: str) -> str:
    return word.strip().lower()


def merge_unique_words(sections: Iterable[list[str]]) -> list[str]:
    merged: OrderedDict[str, None] = OrderedDict()
    for section in sections:
        for word in section:
            normalized = normalize_word(word)
            if normalized:
                merged.setdefault(normalized, None)
    return list(merged.keys())


def build_local_dictionary(words: list[str], base_dictionary: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    local_dictionary: dict[str, dict[str, str]] = {}
    for word in words:
        entry = base_dictionary.get(word, {})
        local_dictionary[word] = {
            "chinese_meaning": entry.get("chinese_meaning", ""),
            "phonetic": entry.get("phonetic", ""),
            "mnemonic": entry.get("mnemonic", "")
        }
    return local_dictionary


def build_word_metadata(words: list[str], base_dictionary: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    for word in words:
        entry = base_dictionary.get(word, {})
        metadata[word] = {
            "chinese_meaning": entry.get("chinese_meaning", ""),
            "phonetic": entry.get("phonetic", ""),
            "mnemonic": entry.get("mnemonic", "")
        }
    return metadata


def main() -> None:
    core_frequency = read_word_list(SOURCE_DIR / "core_frequency.txt")
    cet4 = read_word_list(SOURCE_DIR / "cet4.txt")
    cet6 = read_word_list(SOURCE_DIR / "cet6.txt")
    ielts = read_word_list(SOURCE_DIR / "ielts.txt")
    toefl = read_word_list(SOURCE_DIR / "toefl.txt")
    supplemental = read_word_list(SOURCE_DIR / "supplemental.txt")
    base_dictionary = read_json_dict(SOURCE_DIR / "dictionary_base.json")

    all_words = merge_unique_words([core_frequency, cet4, cet6, ielts, toefl, supplemental, list(base_dictionary.keys())])

    VOCAB_DIR.mkdir(parents=True, exist_ok=True)
    (VOCAB_DIR / "local_dictionary.json").write_text(
        json.dumps(build_local_dictionary(all_words, base_dictionary), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (VOCAB_DIR / "word_metadata.json").write_text(
        json.dumps(build_word_metadata(all_words, base_dictionary), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (VOCAB_DIR / "phrase_meanings.json").write_text(
        json.dumps({}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Merged {len(all_words)} words into LexiMiner vocab files.")


if __name__ == "__main__":
    main()