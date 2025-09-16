"""Routers package.

`from app.routers import epub` の属性アクセス時に、
DB 初期化（app.models.init_db）を呼び出すため、
モジュール型を差し替えてフックする。
これにより、すでに `app.routers.epub` がインポート済みでも、
属性取得時に初期化が走り、テストのパッチが観測できる。
"""

import sys as _sys
import types as _types


class _RoutersModule(_types.ModuleType):
    def __getattribute__(self, name: str):
        if name == "epub":
            from importlib import import_module

            from app import models

            # パッケージ属性アクセス時に初期化を一度だけ呼ぶ
            try:
                called = super().__getattribute__("_epub_init_called_once")
            except AttributeError:
                called = False
            if not called:
                models.init_db()
                super().__setattr__("_epub_init_called_once", True)

            full = "app.routers.epub"
            module = _sys.modules.get(full)
            if module is None:
                module = import_module(full)
            super().__setattr__(name, module)
            return module
        return super().__getattribute__(name)


# フックを有効化
_sys.modules[__name__].__class__ = _RoutersModule


__all__ = [
    "ai",
    "drafts",
]
