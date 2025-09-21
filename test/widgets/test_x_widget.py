from typing import Any, Dict

from app.widget_util import (
    get_widget_default_config,
    process_widget_sync,
    validate_widget_config,
)


def test_x_widget_validate_with_raw_posts() -> None:
    cfg: Dict[str, Any] = get_widget_default_config("x")
    cfg["raw_posts"] = [
        {
            "id": "1",
            "text": "Hello world",
            "author": "alice",
            "created_at": "2024-01-01",
        },
        {"id": "2", "text": "Second line\nMulti-line", "author": "bob"},
    ]
    assert validate_widget_config("x", cfg) is True


def test_x_widget_process_local_format() -> None:
    cfg: Dict[str, Any] = {
        "mode": "thread",
        "max_posts": 5,
        "raw_posts": [
            {
                "id": "1",
                "text": "A first post",
                "author": "alice",
                "created_at": "2024-01-01",
            },
            {"id": "2", "text": "Second", "author": "bob"},
        ],
    }
    out = process_widget_sync("x", cfg)
    assert out is not None
    assert "@alice (2024-01-01)" in out
    assert "> A first post" in out
    assert "@bob" in out
    assert "> Second" in out
