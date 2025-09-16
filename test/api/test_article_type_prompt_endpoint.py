import asyncio
from typing import Any, Literal, Tuple

import pytest

from app.routers.ai import BulletsRequest, from_bullets_prompt


@pytest.mark.parametrize(
    "article_type, expect_url, expect_highlight",
    [
        ("note", False, False),
        ("url", True, False),
        ("review", False, True),
    ],
)
def test_from_bullets_prompt_article_type_sanitization(
    monkeypatch: pytest.MonkeyPatch,
    article_type: Literal["url", "note", "review"],
    expect_url: bool,
    expect_highlight: bool,
) -> None:
    highlight = "これはハイライトのサンプル"
    url = "https://example.com/"

    async def fake_fetch_ctx(u: str) -> Tuple[str | None, str | None]:
        if article_type == "url":
            return "CONTEXT_FROM_URL", None
        # note/review では URL はサニタイズされるため呼ばれない想定
        raise AssertionError("_fetch_url_context should not be called")

    monkeypatch.setattr("app.routers.ai._fetch_url_context", fake_fetch_ctx)

    req = BulletsRequest(
        bullets=["要素A", "要素B"],
        title="サンプル",
        url_context=url,
        highlights=[highlight],
        highlights_asin=[None],
        prompt_template=None,
        article_type=article_type,
    )

    out: Any = asyncio.run(from_bullets_prompt(req))
    prompt: str = str(out.get("prompt", ""))

    if expect_url:
        assert "参照URL:" in prompt
        assert "CONTEXT_FROM_URL" in prompt
    else:
        assert "参照URL:" not in prompt

    if expect_highlight:
        assert highlight in prompt
        # ASIN 記法の断片も（ハイライトが残っていれば）含まれ得る
        assert "参考引用" in prompt
    else:
        assert highlight not in prompt
