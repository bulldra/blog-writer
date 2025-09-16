from typing import Any

__all__ = ["create_app"]


def __getattr__(name: str) -> Any:
    if name == "create_app":
        from .main import create_app  # lazy import

        return create_app
    raise AttributeError(name)
