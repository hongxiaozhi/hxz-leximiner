from __future__ import annotations

import io
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
from flask import Flask, send_from_directory, request

try:
    from core import LexiMinerAnalyzer
    from core.io import load_text_from_upload
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from core import LexiMinerAnalyzer
    from core.io import load_text_from_upload


APP_TITLE = "LexiMiner API"


def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_analyzer() -> LexiMinerAnalyzer:
    project_root = Path(__file__).resolve().parents[1]
    return LexiMinerAnalyzer(project_root=project_root)


def create_app() -> Flask:
    app = Flask(__name__)
    project_root = Path(__file__).resolve().parents[1]
    frontend_dir = project_root / "frontend"

    @app.get("/api/leximiner/health")
    def health() -> tuple[dict, int]:
        return {"status": "ok", "service": APP_TITLE}, 200

    @app.get("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    @app.get("/style.css")
    def style_css():
        return send_from_directory(frontend_dir, "style.css")

    @app.get("/app.js")
    def app_js():
        return send_from_directory(frontend_dir, "app.js")

    @app.get("/frontend/<path:filename>")
    def frontend_assets(filename: str):
        return send_from_directory(frontend_dir, filename)

    @app.post("/api/leximiner/analyze")
    def analyze() -> tuple[dict, int]:
        payload = request.get_json(silent=True) or {}
        form_text = str(request.form.get("text", "")).strip() if request.form else ""
        json_text = str(payload.get("text", "")).strip()
        text = form_text or json_text
        use_online_translation = parse_bool(
            request.form.get("use_online_translation") if request.form else payload.get("use_online_translation", False)
        )

        uploaded_file = request.files.get("file")
        if uploaded_file and uploaded_file.filename:
            try:
                text = load_text_from_upload(uploaded_file)
            except ValueError as exc:
                return {"status": "error", "message": str(exc)}, 400

        if not text:
            return {"status": "error", "message": "text or file is required"}, 400

        analyzer = get_analyzer()
        result = analyzer.analyze_text(text, use_online_translation=use_online_translation)
        word_rows = [item.to_dict() for item in result.words]
        phrase_rows = [item.to_dict() for item in result.phrases]

        word_df = pd.DataFrame(word_rows)
        phrase_df = pd.DataFrame(phrase_rows)

        return {
            "status": "ok",
            "message": "analysis completed",
            "summary": result.summary.__dict__,
            "words": word_rows,
            "phrases": phrase_rows,
            "word_count": len(word_df),
            "phrase_count": len(phrase_df),
        }, 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)