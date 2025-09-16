"""文体分析AI機能のテスト"""

import pytest
from unittest.mock import patch, AsyncMock

from app.ai_utils import analyze_writing_style


@pytest.mark.asyncio
async def test_analyze_writing_style_basic():
    """基本的な文体分析のテスト"""
    sample_text = """
    こんにちは！今日はとても良い天気ですね。
    散歩に出かけてみませんか？きっと気持ちいいですよ。
    新鮮な空気を吸って、リフレッシュしましょう！
    """

    mock_response = {
        "tone": "フレンドリー",
        "formality": "カジュアル",
        "length_preference": "簡潔",
        "target_audience": "一般",
        "writing_style": "親しみやすい",
        "sentence_structure": "短文中心",
        "vocabulary_level": "日常語",
        "emotional_expression": "明るく積極的",
    }

    with patch("app.ai_utils.call_ai", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = str(mock_response)

        result = await analyze_writing_style(sample_text)

        assert result is not None
        assert isinstance(result, dict)
        mock_ai.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_writing_style_formal():
    """フォーマルな文体の分析テスト"""
    sample_text = """
    拝啓　時下ますますご清栄のこととお慶び申し上げます。
    さて、この度は貴重なお時間をいただき、誠にありがとうございます。
    つきましては、下記の件についてご報告させていただきます。
    """

    with patch("app.ai_utils.call_ai", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = '{"tone": "丁寧", "formality": "フォーマル"}'

        result = await analyze_writing_style(sample_text)

        assert result is not None
        mock_ai.assert_called_once()


@pytest.mark.asyncio
async def test_analyze_writing_style_empty_text():
    """空のテキストでの文体分析テスト"""
    result = await analyze_writing_style("")
    assert result is None


@pytest.mark.asyncio
async def test_analyze_writing_style_short_text():
    """短いテキストでの文体分析テスト"""
    result = await analyze_writing_style("こんにちは")
    assert result is None


@pytest.mark.asyncio
async def test_analyze_writing_style_ai_error():
    """AI呼び出しエラーのテスト"""
    sample_text = "これは十分な長さのサンプルテキストです。" * 10

    with patch("app.ai_utils.call_ai", new_callable=AsyncMock) as mock_ai:
        mock_ai.side_effect = Exception("AI service error")

        result = await analyze_writing_style(sample_text)

        assert result is None


@pytest.mark.asyncio
async def test_analyze_writing_style_invalid_json():
    """無効なJSON応答のテスト"""
    sample_text = "これは十分な長さのサンプルテキストです。" * 10

    with patch("app.ai_utils.call_ai", new_callable=AsyncMock) as mock_ai:
        mock_ai.return_value = "This is not valid JSON"

        result = await analyze_writing_style(sample_text)

        assert result is None
