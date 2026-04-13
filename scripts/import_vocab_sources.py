from __future__ import annotations

"""Import reference vocabulary archives into LexiMiner local vocab files."""

import csv
import io
import json
import re
from collections import OrderedDict, defaultdict
from pathlib import Path
from typing import Any
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = PROJECT_ROOT / "data" / "参考词库"
VOCAB_DIR = PROJECT_ROOT / "data" / "vocab"
GENERATED_DIR = VOCAB_DIR / "generated"

WORD_PATTERN = re.compile(r"^[A-Za-z][A-Za-z'-]*$")


def normalize_word(word: str) -> str:
    return word.strip().lower()


def safe_text(value: Any) -> str:
    return str(value or "").strip()


def load_json(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}

    cleaned: dict[str, dict[str, str]] = {}
    for key, value in data.items():
        if not str(key).strip() or not isinstance(value, dict):
            continue
        cleaned[str(key).strip().lower()] = {
            "chinese_meaning": safe_text(value.get("chinese_meaning")),
            "phonetic": safe_text(value.get("phonetic")),
            "mnemonic": safe_text(value.get("mnemonic")),
        }
    return cleaned


def save_json(path: Path, data: dict[str, dict[str, str]]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def add_word(target: OrderedDict[str, None], word: str) -> None:
    normalized = normalize_word(word)
    if normalized and WORD_PATTERN.match(normalized):
        target.setdefault(normalized, None)


def parse_word_text(text: str) -> list[str]:
    entries: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for part in re.split(r"[\s,;|/\t]+", line):
            if WORD_PATTERN.match(part):
                entries.append(part)
    return entries


def extract_word_list_entries(archive: ZipFile) -> list[str]:
    entries: list[str] = []
    for entry in archive.infolist():
        if entry.is_dir():
            continue
        name = entry.filename.lower()
        with archive.open(entry) as raw:
            data = raw.read()

        if name.endswith(".zip"):
            with ZipFile(io.BytesIO(data)) as nested:
                entries.extend(extract_word_list_entries(nested))
            continue

        text = data.decode("utf-8", errors="ignore")
        if name.endswith(".txt"):
            entries.extend(parse_word_text(text))
        elif name.endswith(".json"):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, str):
                        entries.extend(parse_word_text(item))
                    elif isinstance(item, dict):
                        entries.extend(parse_word_text(" ".join(str(v) for v in item.values())))
            elif isinstance(parsed, dict):
                for key, value in parsed.items():
                    entries.extend(parse_word_text(str(key)))
                    if isinstance(value, str):
                        entries.extend(parse_word_text(value))
                    elif isinstance(value, list):
                        for item in value:
                            entries.extend(parse_word_text(str(item)))
        elif name.endswith(".csv"):
            sample = text[:4096]
            try:
                dialect = csv.Sniffer().sniff(sample)
            except Exception:
                dialect = csv.excel
            reader = csv.DictReader(io.StringIO(text), dialect=dialect)
            field_map = {field.lower(): field for field in reader.fieldnames or [] if field}
            word_field = next((field_map[key] for key in ("word", "words", "lemma", "term", "entry", "vocabulary") if key in field_map), None)
            if word_field:
                for row in reader:
                    entries.append(safe_text(row.get(word_field)))
            else:
                plain_reader = csv.reader(io.StringIO(text), dialect=dialect)
                for row in plain_reader:
                    if row:
                        entries.append(safe_text(row[0]))
    return entries


def parse_ecdict_csv(zip_path: Path, local_dictionary: dict[str, dict[str, str]], word_metadata: dict[str, dict[str, str]]) -> int:
    count = 0
    with ZipFile(zip_path) as archive:
        csv_entry = next(
            (entry for entry in archive.infolist() if entry.filename.lower().endswith("ecdict.csv") or entry.filename.lower().endswith("ecdict.mini.csv")),
            None,
        )
        if csv_entry is None:
            return 0

        with archive.open(csv_entry) as raw:
            reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8", errors="ignore", newline=""))
            for row in reader:
                word = normalize_word(row.get("word", ""))
                if not word or not WORD_PATTERN.match(word):
                    continue

                translation = safe_text(row.get("translation"))
                definition = safe_text(row.get("definition"))
                phonetic = safe_text(row.get("phonetic"))
                meaning = translation if translation else (definition.splitlines()[0].strip()[:120] if definition else "")

                entry = {
                    "chinese_meaning": meaning,
                    "phonetic": phonetic if phonetic else f"/{word}/",
                    "mnemonic": f"词典补充：{word}",
                }

                existing = local_dictionary.get(word)
                if existing is None or len(meaning) > len(existing.get("chinese_meaning", "")):
                    local_dictionary[word] = entry
                if word not in word_metadata:
                    word_metadata[word] = entry
                count += 1
    return count


def main() -> None:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    local_dictionary = load_json(VOCAB_DIR / "local_dictionary.json")
    word_metadata = load_json(VOCAB_DIR / "word_metadata.json")
    collector: OrderedDict[str, None] = OrderedDict()
    source_stats: dict[str, int] = defaultdict(int)

    for zip_path in sorted(REFERENCE_DIR.glob("*.zip")):
        if zip_path.name == "ECDICT-master.zip":
            source_stats[zip_path.stem] = parse_ecdict_csv(zip_path, local_dictionary, word_metadata)
        else:
            with ZipFile(zip_path) as archive:
                entries = extract_word_list_entries(archive)
            before = len(collector)
            for word in entries:
                add_word(collector, word)
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

    categories["academic"].update(categories["ielts"])
    categories["academic"].update(categories["toefl"])

    for name, items in categories.items():
        (VOCAB_DIR / f"{name}.txt").write_text("\n".join(sorted(items)), encoding="utf-8")

    save_json(VOCAB_DIR / "local_dictionary.json", local_dictionary)
    save_json(VOCAB_DIR / "word_metadata.json", word_metadata)

    print(f"Imported {len(words)} word-list items and merged {len(local_dictionary)} dictionary entries.")


if __name__ == "__main__":
    main()
