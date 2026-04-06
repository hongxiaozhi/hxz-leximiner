from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd


def build_csv_bytes(word_df: pd.DataFrame, phrase_df: pd.DataFrame) -> bytes:
    """Package word and phrase CSV files into one zip archive."""
    buffer = BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr("words.csv", word_df.to_csv(index=False, encoding="utf-8-sig"))
        zip_file.writestr("phrases.csv", phrase_df.to_csv(index=False, encoding="utf-8-sig"))
    return buffer.getvalue()


def build_excel_bytes(word_df: pd.DataFrame, phrase_df: pd.DataFrame) -> bytes:
    """Export results into a two-sheet Excel workbook."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        word_df.to_excel(writer, sheet_name="words", index=False)
        phrase_df.to_excel(writer, sheet_name="phrases", index=False)
    return buffer.getvalue()