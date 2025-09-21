from typing import Any, Dict, List

import pytest

from app.storage import (
    diff_template_versions,
    get_article_template,
    get_template_version_snapshot,
    list_article_templates,
    list_template_versions,
    save_article_template,
)


@pytest.fixture(autouse=True)
def _init(temp_data_dir):
    # temp_data_dir フィクスチャで初期化済み
    yield


def test_version_history_created_and_deduplicated():
    # 既定テンプレ存在確認
    rows = list_article_templates()
    types = [r.get("type") for r in rows]
    assert "url" in types

    # バージョン履歴は最初は空でも良い（保存で作られる）
    v0: List[Dict[str, Any]] = list_template_versions("url")
    assert isinstance(v0, list)

    # 1回保存で v1 が作られる
    p1: Dict[str, Any] = {
        "name": "URL テンプレ",
        "fields": [
            {"key": "goal", "label": "目的", "input_type": "text"},
            {"key": "url", "label": "URL", "input_type": "text"},
        ],
        "prompt_template": "{{base}}\n---\nURL={{url_context}}",
        "widgets": ["url_context"],
        "mode": "plan",
    }
    save_article_template("url", p1)

    versions1 = list_template_versions("url")
    assert len(versions1) >= 1
    latest_v = versions1[-1]["version"]
    snap = get_template_version_snapshot("url", latest_v)
    assert snap is not None
    assert snap["data"]["prompt_template"].endswith("{{url_context}}")

    # 同一内容で保存してもバージョンは増えない（重複抑制）
    save_article_template("url", p1)
    versions2 = list_template_versions("url")
    assert [v["version"] for v in versions2] == [v["version"] for v in versions1]

    # 内容変更で新バージョン
    p2 = dict(p1)
    p2["prompt_template"] = "changed"
    save_article_template("url", p2)
    versions3 = list_template_versions("url")
    assert len(versions3) == len(versions2) + 1

    # 差分を取得（直前と最新）
    v_prev = versions3[-2]["version"]
    v_latest = versions3[-1]["version"]
    d = diff_template_versions("url", v_prev, v_latest)
    assert "prompt_template" in d["changed_keys"]
    assert d["diff"]["prompt_template"]["from"] != d["diff"]["prompt_template"]["to"]


def test_snapshot_not_found_returns_none():
    assert get_template_version_snapshot("doesnotexist", 1) is None
    # テンプレが存在しても不正バージョンなら None
    at = get_article_template("url")
    assert at is not None
    assert get_template_version_snapshot("url", 999999) is None
