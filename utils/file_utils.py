from __future__ import annotations

from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


def load_text_from_upload(uploaded_file) -> str:
    """Read supported uploaded files into plain text."""
    suffix = Path(uploaded_file.name).suffix.lower()
    file_bytes = uploaded_file.getvalue()

    if suffix == ".txt":
        return file_bytes.decode("utf-8", errors="ignore")

    if suffix == ".pdf":
        return extract_text_from_pdf(file_bytes)

    raise ValueError("当前版本仅支持上传 .txt 和 .pdf 文件。")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using pypdf."""
    reader = PdfReader(BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(page.strip() for page in pages if page.strip())
    if not text.strip():
        raise ValueError("PDF 中未提取到可用文本，可能是扫描版 PDF 或内容为空。")
    return text