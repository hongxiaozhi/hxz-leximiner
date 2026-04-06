from pathlib import Path

from services.analysis_service import AnalysisService


def test_analysis_service_basic_flow() -> None:
    project_root = Path(__file__).resolve().parents[1]
    service = AnalysisService(
        vocab_dir=project_root / "data" / "vocab",
        output_dir=project_root / "output",
    )

    result = service.analyze_text(
        "Academic research improves learning outcomes. Academic reading improves writing skills."
    )

    assert result.summary.unique_words > 0
    assert any(item.lemma == "academic" and item.category == "academic" for item in result.words)
    academic_word = next(item for item in result.words if item.lemma == "academic")
    assert academic_word.chinese_meaning
    assert academic_word.phonetic
    assert academic_word.mnemonic
    assert academic_word.chinese_meaning == "学术的；学院的"
    assert len(result.phrases) > 0