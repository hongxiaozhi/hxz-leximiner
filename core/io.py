from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
from pypdf import PdfReader


def build_csv_bytes(word_df: pd.DataFrame, phrase_df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr("words.csv", word_df.to_csv(index=False, encoding="utf-8-sig"))
        zip_file.writestr("phrases.csv", phrase_df.to_csv(index=False, encoding="utf-8-sig"))
    return buffer.getvalue()


def build_excel_bytes(word_df: pd.DataFrame, phrase_df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        word_df.to_excel(writer, sheet_name="words", index=False)
        phrase_df.to_excel(writer, sheet_name="phrases", index=False)
    return buffer.getvalue()


def load_text_from_upload(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix.lower()
    file_bytes = uploaded_file.getvalue()

    if suffix == ".txt":
        return file_bytes.decode("utf-8", errors="ignore")

    if suffix == ".pdf":
        return extract_text_from_pdf(file_bytes)

    raise ValueError("当前版本仅支持上传 .txt 和 .pdf 文件。")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(page.strip() for page in pages if page.strip())
    if not text.strip():
        raise ValueError("PDF 中未提取到可用文本，可能是扫描版 PDF 或内容为空。")
    return text