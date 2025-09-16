"""Obsidian設定拡張のテスト"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.obsidian import (
    ObsidianConfig,
    collect_articles,
    collect_highlights,
    find_obsidian_articles_dir,
    find_obsidian_highlights_dir,
    get_configured_obsidian_config,
    set_configured_obsidian_config,
)


@pytest.fixture
def temp_obsidian_structure():
    """テスト用のObsidian構造を作成"""
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)

        # ディレクトリ構造作成
        articles_dir = root / "articles"
        highlights_dir = root / "kindle_highlights"
        articles_dir.mkdir()
        highlights_dir.mkdir()

        # 記事ファイル作成
        (articles_dir / "article1.md").write_text(
            "# Article 1\n\nThis is a test article.", encoding="utf-8"
        )
        (articles_dir / "article2.md").write_text(
            "# Article 2\n\nAnother test article.", encoding="utf-8"
        )

        # ハイライトファイル作成
        (highlights_dir / "book1.md").write_text(
            "---\ntitle: Test Book\nauthor: Test Author\n---\n\n"
            "> This is a highlight from Kindle\n\nLocation: 100-101",
            encoding="utf-8",
        )

        yield {
            "root": root,
            "articles_dir": articles_dir,
            "highlights_dir": highlights_dir,
        }


@pytest.fixture
def temp_settings(temp_obsidian_structure):
    """テスト用の設定ファイル"""
    with tempfile.TemporaryDirectory() as settings_dir:
        settings_path = Path(settings_dir) / "settings.json"

        with patch("app.obsidian._settings_path", return_value=settings_path):
            yield {
                "settings_path": settings_path,
                "obsidian_root": temp_obsidian_structure["root"],
            }


def test_obsidian_config_dataclass(temp_obsidian_structure):
    """ObsidianConfigデータクラスのテスト"""
    root = temp_obsidian_structure["root"]
    config = ObsidianConfig(root_dir=root)

    assert config.root_dir == root
    assert config.articles_dir == "articles"
    assert config.highlights_dir == "kindle_highlights"
    assert config.articles_path == root / "articles"
    assert config.highlights_path == root / "kindle_highlights"


def test_obsidian_config_custom_dirs(temp_obsidian_structure):
    """カスタムディレクトリ設定のテスト"""
    root = temp_obsidian_structure["root"]
    config = ObsidianConfig(
        root_dir=root,
        articles_dir="custom_articles",
        highlights_dir="custom_highlights",
    )

    assert config.articles_dir == "custom_articles"
    assert config.highlights_dir == "custom_highlights"
    assert config.articles_path == root / "custom_articles"
    assert config.highlights_path == root / "custom_highlights"


def test_set_and_get_configured_obsidian_config(temp_settings):
    """設定の保存と読み込みのテスト"""
    root_dir = str(temp_settings["obsidian_root"])

    # 設定を保存
    config = set_configured_obsidian_config(root_dir, "my_articles", "my_highlights")

    assert config is not None
    assert config.root_dir == Path(root_dir)
    assert config.articles_dir == "my_articles"
    assert config.highlights_dir == "my_highlights"

    # 設定を読み込み
    loaded_config = get_configured_obsidian_config()
    assert loaded_config is not None
    assert loaded_config.root_dir == Path(root_dir)
    assert loaded_config.articles_dir == "my_articles"
    assert loaded_config.highlights_dir == "my_highlights"


def test_set_configured_obsidian_config_invalid_dir():
    """無効なディレクトリ指定のテスト"""
    with patch(
        "app.obsidian._settings_path", return_value=Path("/tmp/test_settings.json")
    ):
        with pytest.raises(OSError, match="Invalid directory"):
            set_configured_obsidian_config("/nonexistent/directory")


def test_set_configured_obsidian_config_clear(temp_settings):
    """設定クリアのテスト"""
    root_dir = str(temp_settings["obsidian_root"])

    # 設定を保存してからクリア
    set_configured_obsidian_config(root_dir)
    config = set_configured_obsidian_config(None)

    assert config is None
    assert get_configured_obsidian_config() is None


def test_legacy_settings_compatibility(temp_settings):
    """旧設定形式との互換性テスト"""
    settings_path = temp_settings["settings_path"]
    root_dir = temp_settings["obsidian_root"]

    # 旧形式で設定を保存
    settings_path.write_text(
        json.dumps({"obsidian_dir": str(root_dir)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 旧設定から読み込めることを確認
    config = get_configured_obsidian_config()
    assert config is not None
    assert config.root_dir == root_dir
    assert config.articles_dir == "articles"  # デフォルト値
    assert config.highlights_dir == "kindle_highlights"  # デフォルト値


def test_collect_articles(temp_obsidian_structure):
    """記事収集のテスト"""
    articles_dir = temp_obsidian_structure["articles_dir"]
    articles = collect_articles(articles_dir)

    assert len(articles) == 2
    article_names = {article.stem for article in articles}
    assert article_names == {"article1", "article2"}


def test_collect_highlights(temp_obsidian_structure):
    """ハイライト収集のテスト"""
    highlights_dir = temp_obsidian_structure["highlights_dir"]
    highlights = collect_highlights(highlights_dir)

    assert len(highlights) > 0
    highlight = highlights[0]
    assert highlight.book == "Test Book"
    assert highlight.author == "Test Author"
    assert "This is a highlight from Kindle" in highlight.text


def test_find_directories_with_config(temp_settings):
    """設定ありでのディレクトリ検索テスト"""
    root_dir = str(temp_settings["obsidian_root"])

    # 設定を保存
    set_configured_obsidian_config(root_dir, "articles", "kindle_highlights")

    # ディレクトリが正しく見つかることを確認
    articles_dir = find_obsidian_articles_dir()
    highlights_dir = find_obsidian_highlights_dir()

    assert articles_dir == Path(root_dir) / "articles"
    assert highlights_dir == Path(root_dir) / "kindle_highlights"


def test_find_directories_without_config(temp_obsidian_structure):
    """設定なしでのディレクトリ検索テスト"""
    with patch("app.obsidian.get_configured_obsidian_config", return_value=None):
        with patch("app.obsidian.find_obsidian_dir", return_value=None):
            articles_dir = find_obsidian_articles_dir()
            highlights_dir = find_obsidian_highlights_dir()

            assert articles_dir is None
            assert highlights_dir is None
