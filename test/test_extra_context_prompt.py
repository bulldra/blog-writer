import asyncio

from app.routers.ai import BulletsRequest, from_bullets_prompt


def test_extra_context_is_injected_into_template():
    req = BulletsRequest(
        bullets=["A"],
        title=None,
        style=None,
        length=None,
        url_context=None,
        highlights=None,
        highlights_asin=None,
        prompt_template="{{base}}\ngoal={{goal}}\naud={{audience}}\ncustom={{x}}",
        article_type="note",
        extra_context={"goal": "書く目的", "audience": "エンジニア", "x": "OK"},
    )
    out = asyncio.run(from_bullets_prompt(req))
    prompt = out.get("prompt", "")
    assert "goal=書く目的" in prompt
    assert "aud=エンジニア" in prompt
    assert "custom=OK" in prompt
