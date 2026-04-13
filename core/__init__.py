from __future__ import annotations

from pathlib import Path

from core.analyzer import LexiMinerAnalyzer
from core.io import build_csv_bytes, build_excel_bytes, extract_text_from_pdf, load_text_from_upload


class LexiMinerCore:
    """Unified facade for parsing, analyzing, and exporting LexiMiner results."""

    def __init__(self, project_root: Path | None = None) -> None:
        # 这里保留一个稳定入口，外部只需要记住这个 facade，
        # 不用关心具体是哪个子模块在处理。
        self.project_root = project_root or Path(__file__).resolve().parents[1]
        self.analyzer = LexiMinerAnalyzer(project_root=self.project_root)

    def analyze_text(self, text: str, use_online_translation: bool = False):
        return self.analyzer.analyze_text(text, use_online_translation=use_online_translation)

    def analyze_upload(self, uploaded_file, use_online_translation: bool = False):
        text = load_text_from_upload(uploaded_file)
        return self.analyze_text(text, use_online_translation=use_online_translation)

    def analyze_path(self, file_path: str | Path, use_online_translation: bool = False):
        # 本地调试时可以直接传文件路径；这里把路径包装成和 Flask
        # 上传对象一致的结构，方便复用同一套分析逻辑。
        path = Path(file_path)
        upload = _PathUpload(path)
        return self.analyze_upload(upload, use_online_translation=use_online_translation)

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        return extract_text_from_pdf(file_bytes)

    def build_csv_bytes(self, word_df, phrase_df) -> bytes:
        return build_csv_bytes(word_df, phrase_df)

    def build_excel_bytes(self, word_df, phrase_df) -> bytes:
        return build_excel_bytes(word_df, phrase_df)


class _PathUpload:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.filename = path.name
        self.name = path.name
        self.mimetype = self._guess_mimetype(path)
        self._data = path.read_bytes()
        self._cursor = 0

    def read(self) -> bytes:
        return self._data

    def seek(self, pos: int) -> None:
        self._cursor = pos

    @staticmethod
    def _guess_mimetype(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return "application/pdf"
        if suffix == ".txt":
            return "text/plain"
        return "application/octet-stream"


__all__ = [
    "LexiMinerAnalyzer",
    "LexiMinerCore",
    "load_text_from_upload",
    "extract_text_from_pdf",
    "build_csv_bytes",
    "build_excel_bytes",
]
