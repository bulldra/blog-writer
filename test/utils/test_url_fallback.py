import asyncio

from app.routers.ai import _fetch_url_context


def test_fetch_url_context_denied_scheme():
    text, err = asyncio.run(_fetch_url_context("file:///etc/passwd"))
    assert text is None
    assert err == "url_not_allowed"


def test_fetch_url_context_invalid_host():
    text, err = asyncio.run(
        _fetch_url_context("http://169.254.169.254/latest/meta-data/")
    )
    assert text is None
    assert err in {"url_not_allowed", "ConnectError", "RequestError", "HTTPError"}


def test_fetch_url_context_timeout():
    # 過度な遅延や拒否が起きうるRFC1918アドレス。
    text, err = asyncio.run(_fetch_url_context("http://10.255.255.1/"))
    assert text is None
    assert err is not None
