from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
import sys

import pandas as pd

try:
    from services.analysis_service import AnalysisService
    from utils.export_utils import build_csv_bytes, build_excel_bytes
    from utils.file_utils import load_text_from_upload
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent)) 
    from services.analysis_service import AnalysisService
    from utils.export_utils import build_csv_bytes, build_excel_bytes
    from utils.file_utils import load_text_from_upload


APP_TITLE = "LexiMiner"


@lru_cache(maxsize=1)
def get_analysis_service() -> AnalysisService:
    vocab_dir = Path(__file__).parent / "data" / "vocab"
    output_dir = Path(__file__).parent / "output"
    return AnalysisService(vocab_dir=vocab_dir, output_dir=output_dir)


def render_download_buttons(st, word_df: pd.DataFrame, phrase_df: pd.DataFrame) -> None:
    csv_bytes = build_csv_bytes(word_df, phrase_df)
    excel_bytes = build_excel_bytes(word_df, phrase_df)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="导出 CSV",
            data=csv_bytes,
            file_name="leximiner_results.zip",
            mime="application/zip",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            label="导出 Excel",
            data=excel_bytes,
            file_name="leximiner_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def main() -> None:
    import streamlit as st

    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title("LexiMiner - 英语词汇与短语智能提取分类系统")
    st.caption("MVP 版本：支持英文文本分析、词汇分类、短语提取与 CSV/Excel 导出")

    service = get_analysis_service()

    default_text = (
        "LexiMiner helps students analyze academic reading materials. "
        "The system extracts important words and common phrases from English texts."
    )

    uploaded_file = st.file_uploader("上传英文文本文件（支持 .txt / .pdf）", type=["txt", "pdf"])
    text_input = st.text_area("请输入或粘贴英文文本", value=default_text, height=220)
    use_online_translation = st.checkbox(
        "联网补充中文释义（较慢，默认关闭）",
        value=False,
        help="关闭时优先使用本地词典和离线回退逻辑，分析速度更稳定。",
    )

    if uploaded_file is not None:
        try:
            text_input = load_text_from_upload(uploaded_file)
            st.success(f"已读取文件：{uploaded_file.name}")
        except ValueError as exc:
            st.error(str(exc))

    if st.button("开始分析", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("请输入英文文本，或上传一个 .txt / .pdf 文件。")
            return

        with st.spinner("正在分析文本，请稍候..."):
            result = service.analyze_text(
                text_input,
                use_online_translation=use_online_translation,
            )

        word_df = pd.DataFrame([item.to_dict() for item in result.words])
        phrase_df = pd.DataFrame([item.to_dict() for item in result.phrases])

        st.subheader("分析概览")
        summary_cols = st.columns(4)
        summary_cols[0].metric("总词条数", result.summary.total_words)
        summary_cols[1].metric("去重词条数", result.summary.unique_words)
        summary_cols[2].metric("短语数量", result.summary.total_phrases)
        summary_cols[3].metric("句子数量", result.summary.total_sentences)

        st.subheader("词汇结果")
        st.dataframe(word_df, use_container_width=True, hide_index=True)

        st.subheader("短语结果")
        st.dataframe(phrase_df, use_container_width=True, hide_index=True)

        st.subheader("分类统计")
        category_counts = word_df["category"].value_counts().rename_axis("category").reset_index(name="count")
        st.bar_chart(category_counts.set_index("category"))

        render_download_buttons(st, word_df, phrase_df)


if __name__ == "__main__":
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except ModuleNotFoundError:
        get_script_run_ctx = None

    if get_script_run_ctx is None or get_script_run_ctx() is None:
        from streamlit.web import cli as stcli

        sys.argv = ["streamlit", "run", str(Path(__file__).resolve())]
        raise SystemExit(stcli.main())

    main()