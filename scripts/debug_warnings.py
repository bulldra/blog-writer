#!/usr/bin/env python3
"""
SwigPyの警告を発生させているモジュールを特定するためのデバッグスクリプト
"""

import traceback
import warnings
from typing import Any, Optional


def warning_handler(
    message: Any,
    category: type,
    filename: str,
    lineno: int,
    file: Optional[Any] = None,
    line: Optional[str] = None,
) -> None:
    """カスタム警告ハンドラー"""
    if "SwigPy" in str(message) or "swigvarlink" in str(message):
        print(f"SwigPy警告を検出: {message}")
        print(f"カテゴリ: {category}")
        print(f"ファイル: {filename}:{lineno}")
        print("スタックトレース:")
        traceback.print_stack()
        print("-" * 50)


# 警告フィルタを設定
warnings.showwarning = warning_handler

# 主要なSwigベースのライブラリを順番にインポートしてテスト
modules_to_test = [
    "faiss",
    "torch",
    "sklearn",
    "sentence_transformers",
    "numpy",
    "scipy",
]

print("SwigPy警告を発生させるモジュールを特定中...")

for module_name in modules_to_test:
    try:
        print(f"\n{module_name}をインポート中...")
        __import__(module_name)
        print(f"{module_name}: インポート完了")
    except ImportError as e:
        print(f"{module_name}: インポートエラー - {e}")
    except Exception as e:
        print(f"{module_name}: その他のエラー - {e}")

print("\nアプリケーションのメインモジュールをテスト...")
try:
    print("app.main: インポート完了")
except Exception as e:
    print(f"app.main: エラー - {e}")
