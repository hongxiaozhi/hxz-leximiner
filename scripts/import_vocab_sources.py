from __future__ import annotations

"""Import reference vocabulary archives into LexiMiner's vocab layer."""

import csv
import io
import json
import re
from collections import OrderedDict, defaultdict
from pathlib import Path
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = PROJECT_ROOT / "data" / "参考词库"
VOCAB_DIR = PROJECT_ROOT / "data" / "vocab"
GENERATED_DIR = VOCAB_DIR / "generated"

WORD_PATTERN = re.compile(r"^[A-Za-z][A-Za-z'-]*$")
WORD_FIELD_NAMES = {"word", "words", "lemma", "term", "entry", "vocabulary"}


def normalize_word(word: str) -> str:
    return word.strip().lower()


def add_words(target: OrderedDict[str, None], words: list[str]) -> None:
    for word in words:
        normalized = normalize_word(word)
        if normalized and WORD_PATTERN.match(normalized):
            target.setdefault(normalized, None)


def words_from_text(text: str) -> list[str]:
    words: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"[\s,;|/\t]+", line)
        for part in parts:
            part = part.strip()
            if WORD_PATTERN.match(part):
                words.append(part)
    return words


def words_from_json(text: str) -> list[str]:
    data = json.loads(text)
    words: list[str] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                words.extend(words_from_text(item))
            elif isinstance(item, dict):
                for value in item.values():
                    if isinstance(value, str):
                        words.extend(words_from_text(value))
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(key, str):
                words.extend(words_from_text(key))
            if isinstance(value, str):
                words.extend(words_from_text(value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        words.extend(words_from_text(item))
    return words


def words_from_csv(text: str) -> list[str]:
    words: list[str] = []
    if not text.strip():
        return words

    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample)
    except Exception:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if reader.fieldnames:
        normalized_fields = {field.strip().lower(): field for field in reader.fieldnames if field}
        target_field = next((normalized_fields[name] for name in WORD_FIELD_NAMES if name in normalized_fields), None)
        if target_field:
            for row in reader:
                cell = str(row.get(target_field, "")).strip()
                if WORD_PATTERN.match(cell):
                    words.append(cell)
            return words

    reader_plain = csv.reader(io.StringIO(text), dialect=dialect)
    for row in reader_plain:
        if row:
            cell = str(row[0]).strip()
            if WORD_PATTERN.match(cell):
                words.append(cell)
    return words


def extract_archive_words(archive: ZipFile, collector: OrderedDict[str, None]) -> None:
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            name = entry.filename.lower()
            data = archive.read(entry)
            if name.endswith(".zip"):
                with ZipFile(io.BytesIO(data)) as nested_archive:
                    extract_archive_words(nested_archive, collector)
                continue
            text = data.decode("utf-8", errors="ignore")
            if name.endswith(".txt"):
                add_words(collector, words_from_text(text))
            elif name.endswith(".json"):
                try:
                    add_words(collector, words_from_json(text))
                except Exception:
                    pass
            elif name.endswith(".csv"):
                add_words(collector, words_from_csv(text))


def extract_zip_words(zip_path: Path, collector: OrderedDict[str, None]) -> None:
    with ZipFile(zip_path) as archive:
        extract_archive_words(archive, collector)


def build_phrase_words() -> dict[str, str]:
    phrase_file = VOCAB_DIR / "phrase_dict.txt"
    phrases: dict[str, str] = {}
    if phrase_file.exists():
        for line in phrase_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            phrases[line.lower()] = line
    return phrases


def main() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    collector: OrderedDict[str, None] = OrderedDict()
    source_stats: dict[str, int] = defaultdict(int)

    for zip_path in sorted(REFERENCE_DIR.glob("*.zip")):
        before = len(collector)
        extract_zip_words(zip_path, collector)
        source_stats[zip_path.stem] = len(collector) - before

    words = list(collector.keys())
    (GENERATED_DIR / "all_words.txt").write_text("\n".join(words), encoding="utf-8")
    (GENERATED_DIR / "source_stats.json").write_text(json.dumps(source_stats, ensure_ascii=False, indent=2), encoding="utf-8")

    categories = {
        "high_school": set(),
        "cet4": set(),
        "cet6": set(),
        "ielts": set(),
        "toefl": set(),
        "academic": set(),
    }

    for word in words:
        if len(word) <= 4:
            categories["high_school"].add(word)
        elif len(word) <= 6:
            categories["cet4"].add(word)
        elif len(word) <= 8:
            categories["cet6"].add(word)
        elif len(word) <= 10:
            categories["ielts"].add(word)
        else:
            categories["toefl"].add(word)

    # Academic words are the intersection of the longer and more formal lists.
    categories["academic"].update(categories["ielts"])
    categories["academic"].update(categories["toefl"])

    for name, items in categories.items():
        (VOCAB_DIR / f"{name}.txt").write_text("\n".join(sorted(items)), encoding="utf-8")

    (VOCAB_DIR / "phrase_meanings.json").write_text(
        json.dumps(build_phrase_words(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Imported {len(words)} words from {len(list(REFERENCE_DIR.glob('*.zip')))} archives.")


if __name__ == "__main__":
    main()