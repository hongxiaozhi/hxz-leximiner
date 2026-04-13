from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make sure the project root is importable no matter where this script is launched from.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core import LexiMinerCore


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug LexiMiner core parsing and analysis locally.")
    parser.add_argument(
        "file_path",
        nargs="?",
        help="要测试的 .txt 或 .pdf 文件路径；不传则使用默认路径。",
    )
    args = parser.parse_args()

    default_path = r"e:\QiuJiwei\hxz\hxz-leximiner\tests\cet6_2025_06_1.pdf"
    raw_path = args.file_path or default_path
    file_path = Path(raw_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    core = LexiMinerCore(project_root=PROJECT_ROOT)

    # 直接走统一接口，和实际调用保持一致。
    print(f"[1/2] 分析文件: {file_path}")
    result = core.analyze_path(file_path)

    print("[2/2] 分析结果摘要:")
    print(result.summary)
    print(f"words: {len(result.words)}")
    print(f"phrases: {len(result.phrases)}")

    print("\n前 10 个单词:")
    for item in result.words[:10]:
        print(item.to_dict())

    print("\n前 10 个短语:")
    for item in result.phrases[:10]:
        print(item.to_dict())


if __name__ == "__main__":
    main()
