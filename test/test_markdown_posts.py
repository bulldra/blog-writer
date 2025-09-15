import shutil
from pathlib import Path

from app.storage import (
    DATA_DIR,
    POSTS_DIR,
    delete_markdown_post,
    delete_prompt_template,
    init_storage,
    list_markdown_posts,
    list_prompt_templates,
    read_markdown_post,
    save_markdown_post,
    save_prompt_template,
)


def setup_module(module):
    # テスト用にデータディレクトリを空に
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    init_storage()


def test_save_and_list_and_read_markdown_post(tmp_path: Path):
    # 1件保存
    content = "# タイトル\n本文一行目\n"
    info = save_markdown_post(content, git_commit=False)
    assert info["filename"].endswith(".md")
    assert (POSTS_DIR / info["filename"]).exists()

    # 一覧取得
    lst = list_markdown_posts()
    assert len(lst) >= 1
    found = next((x for x in lst if x["filename"] == info["filename"]), None)
    assert found is not None
    assert found["title"].startswith("タイトル")

    # 読み取り
    body = read_markdown_post(info["filename"]) or ""
    assert "本文一行目" in body


def test_read_invalid_filename_returns_none():
    assert read_markdown_post("../../etc/passwd") is None
    assert read_markdown_post("not-exist.md") is None


def test_delete_markdown_post(tmp_path: Path):
    content = "# 削除テスト\n本文\n"
    info = save_markdown_post(content, git_commit=False)
    filename = info["filename"]
    assert (POSTS_DIR / filename).exists()

    ok = delete_markdown_post(filename)
    assert ok is True
    assert not (POSTS_DIR / filename).exists()

    # 二度目は False
    ok2 = delete_markdown_post(filename)
    assert ok2 is False


def test_prompt_templates_crud(tmp_path: Path, monkeypatch):
    # データディレクトリを置き換え
    monkeypatch.setenv("BLOGWRITER_DATA_DIR", str(tmp_path))
    init_storage()

    # 初期は空
    assert list_prompt_templates() == []

    # 追加
    row1 = save_prompt_template("A", "content-a")
    assert row1 == {"name": "A", "content": "content-a"}
    assert list_prompt_templates()[:1] == [row1]

    # 上書き
    row1b = save_prompt_template("A", "content-a2")
    assert row1b["content"] == "content-a2"
    items = list_prompt_templates()
    assert any(it["name"] == "A" and it["content"] == "content-a2" for it in items)

    # 別テンプレ追加（先頭に入る）
    row2 = save_prompt_template("B", "bb")
    assert row2 == {"name": "B", "content": "bb"}
    items2 = list_prompt_templates()
    assert items2[0]["name"] == "B"

    # 削除
    ok = delete_prompt_template("A")
    assert ok is True
    assert not any(it["name"] == "A" for it in list_prompt_templates())
