from __future__ import annotations

import pytest
from pytest_mock import MockerFixture

from news_service.content_generator import ContentGenerator


class TestContentGenerator:
    """测试 ContentGenerator 的 LLM 调用与响应解析。"""

    @pytest.fixture
    def generator(self) -> ContentGenerator:
        return ContentGenerator(
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4o",
        )

    @pytest.mark.asyncio
    async def test_generate_post_success(
        self, generator: ContentGenerator, mocker: MockerFixture,
    ) -> None:
        mock_response = mocker.AsyncMock()
        mock_response.choices = [
            mocker.MagicMock(
                message=mocker.MagicMock(
                    content="BASE_ASSET: BTC\nCONTENT: 🚀 Bitcoin just hit $100K!",
                ),
            ),
        ]
        mock_client = mocker.AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        generator._openai_client = mock_client

        base_asset, content = await generator.generate_post(
            "Bitcoin Surges", "BTC reaches new highs",
        )
        assert base_asset == "BTC"
        assert content == "🚀 Bitcoin just hit $100K!"

    @pytest.mark.asyncio
    async def test_generate_post_default_base_asset(
        self, generator: ContentGenerator, mocker: MockerFixture,
    ) -> None:
        """当 LLM 未返回 BASE_ASSET 时，应使用默认值 CRYPTO。"""
        mock_response = mocker.AsyncMock()
        mock_response.choices = [
            mocker.MagicMock(
                message=mocker.MagicMock(
                    content="CONTENT: Just some crypto news!",
                ),
            ),
        ]
        mock_client = mocker.AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        generator._openai_client = mock_client

        base_asset, content = await generator.generate_post(
            "Crypto News", "Some content",
        )
        assert base_asset == "CRYPTO"
        assert content == "Just some crypto news!"

    @pytest.mark.asyncio
    async def test_generate_post_llm_failure_fallback(
        self, generator: ContentGenerator, mocker: MockerFixture,
    ) -> None:
        """LLM 调用失败时应有 fallback 逻辑。"""
        mock_client = mocker.AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        generator._openai_client = mock_client

        base_asset, content = await generator.generate_post(
            "Bitcoin News", "BTC content here",
        )
        assert base_asset == "CRYPTO"
        assert "Bitcoin News" in content
        assert "BTC content here" in content

    def test_parse_response_with_both_fields(self, generator: ContentGenerator) -> None:
        base_asset, content = generator._parse_response(
            "BASE_ASSET: ETH\nCONTENT: Ethereum is soaring!",
        )
        assert base_asset == "ETH"
        assert content == "Ethereum is soaring!"

    def test_parse_response_content_only(self, generator: ContentGenerator) -> None:
        base_asset, content = generator._parse_response("Just a simple post")
        assert base_asset == "CRYPTO"
        assert content == "Just a simple post"

    def test_parse_response_multiline_content(self, generator: ContentGenerator) -> None:
        response = """BASE_ASSET: SOL
CONTENT: Solana is heating up!
More details here."""
        base_asset, content = generator._parse_response(response)
        assert base_asset == "SOL"
        assert content == "Solana is heating up!"

    def test_parse_response_base_asset_after_content(self, generator: ContentGenerator) -> None:
        """CONTENT 在前、BASE_ASSET 在后时也能正确解析。"""
        response = """CONTENT: Great news for crypto!
BASE_ASSET: BTC"""
        base_asset, content = generator._parse_response(response)
        assert base_asset == "BTC"
        assert content == "Great news for crypto!"
