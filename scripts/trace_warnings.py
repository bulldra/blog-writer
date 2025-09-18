#!/usr/bin/env python3
"""
SwigPy警告を発生させているライブラリを詳細にトレースするスクリプト
"""

import sys
import traceback
import warnings
from typing import Any, Optional


def detailed_warning_handler(
    message: Any,
    category: type,
    filename: str,
    lineno: int,
    file: Optional[Any] = None,
    line: Optional[str] = None,
) -> None:
    """詳細な警告ハンドラー"""
    if (
        "SwigPy" in str(message)
        or "swigvarlink" in str(message)
        or "__module__ attribute" in str(message)
    ):
        print("=== SwigPy警告検出 ===")
        print(f"メッセージ: {message}")
        print(f"カテゴリ: {category}")
        print(f"ファイル: {filename}:{lineno}")
        print(f"行: {line}")
        print("フルスタックトレース:")
        for entry in traceback.format_stack():
            print(entry.strip())
        print("=" * 50)


# カスタム警告ハンドラーを設定
warnings.showwarning = detailed_warning_handler

# すべてのDeprecationWarningを表示するように設定
warnings.filterwarnings("always", category=DeprecationWarning)

print("段階的にライブラリをインポートして警告の発生源を特定中...")

# 段階的にインポート
modules_to_test = [
    ("numpy", "import numpy"),
    ("scipy", "import scipy"),
    ("sklearn", "import sklearn"),
    ("torch", "import torch"),
    ("faiss", "import faiss"),
    ("sentence_transformers", "import sentence_transformers"),
]

for name, import_stmt in modules_to_test:
    print(f"\n--- {name}をインポート中 ---")
    try:
        exec(import_stmt)
        print(f"{name}: インポート完了")
    except ImportError as e:
        print(f"{name}: インポートエラー - {e}")
    except Exception as e:
        print(f"{name}: その他のエラー - {e}")

print("\n--- アプリケーションモジュールのインポート ---")
try:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print("app.main: インポート完了")
except Exception as e:
    print(f"app.main: エラー - {e}")
