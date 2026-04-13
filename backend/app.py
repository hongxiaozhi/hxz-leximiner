from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from flask import Flask, send_from_directory, request

try:
    from core import LexiMinerAnalyzer
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from core import LexiMinerAnalyzer


APP_TITLE = "LexiMiner API"


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
        text = str(payload.get("text", "")).strip()
        use_online_translation = bool(payload.get("use_online_translation", False))

        if not text:
            return {"status": "error", "message": "text is required"}, 400

        analyzer = get_analyzer()
        result = analyzer.analyze_text(text, use_online_translation=use_online_translation)

        return {
            "status": "ok",
            "message": "analysis completed",
            "summary": result.summary.__dict__,
            "words": [item.to_dict() for item in result.words],
            "phrases": [item.to_dict() for item in result.phrases],
        }, 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)