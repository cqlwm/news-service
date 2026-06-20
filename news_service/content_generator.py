from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = "你是一个专业的加密货币新闻编辑，擅长将新闻改写为社交媒体贴文。"

DEFAULT_USER_TEMPLATE = """请将以下新闻改写为适合社交媒体发布的贴文格式：

要求：
1. 简洁有力，吸引眼球
2. 在开头明确指出主要涉及的加密货币（格式：$BTC $ETH 等），如果有多个最多3个
3. 长度控制在200字以内
4. 语气专业但不失活泼
5. 可以适当的添加一些emoji让内容更生动

新闻标题：{title}
新闻内容：{content}

请按以下格式返回：
BASE_ASSET: BTC
CONTENT: 这里是贴文内容..."""


class ConfigError(Exception):
    """配置不完整导致的错误。"""
    pass


class ContentGenerator:
    """AI 内容生成器。

    将新闻改写为社交媒体贴文。OpenAI 客户端采用懒加载，
    仅在首次调用 generate_post 时创建，避免启动时因缺少 API key 而崩溃。
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self.model = model
        self.system_prompt: str = DEFAULT_SYSTEM_PROMPT
        self.user_template: str = DEFAULT_USER_TEMPLATE
        self._openai_client = None

    @property
    def is_configured(self) -> bool:
        """检查 LLM 配置是否完整。"""
        return bool(self._api_key) and bool(self.model)

    def update_config(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        system_prompt: str | None = None,
        user_template: str | None = None,
    ) -> None:
        """运行时更新配置。当 API key 或 base URL 变化时，重建客户端。"""
        changed = False
        if api_key is not None and api_key != self._api_key:
            self._api_key = api_key
            changed = True
        if base_url is not None and base_url != self._base_url:
            self._base_url = base_url
            changed = True
        if model is not None:
            self.model = model
        if system_prompt is not None:
            self.system_prompt = system_prompt
        if user_template is not None:
            self.user_template = user_template
        if changed:
            self._openai_client = None
            logger.info("ContentGenerator client recreated due to config change")

    def _get_client(self):
        if not self._api_key:
            raise ConfigError(
                "OpenAI API Key 未配置。请在设置页面配置 API Key 后重试。"
            )
        if self._openai_client is None:
            from openai import AsyncOpenAI

            self._openai_client = AsyncOpenAI(
                api_key=self._api_key, base_url=self._base_url
            )
        return self._openai_client

    async def generate_post(self, title: str, content: str) -> tuple[str, str]:
        """生成社交媒体贴文。

        Raises:
            ConfigError: API Key 或 Model 未配置时抛出。
        """
        if not self.is_configured:
            missing = []
            if not self._api_key:
                missing.append("API Key")
            if not self.model:
                missing.append("Model")
            raise ConfigError(
                f"LLM 配置不完整，缺少: {', '.join(missing)}。"
                "请在设置页面完成配置。"
            )

        prompt = self.user_template.format(title=title, content=content[:1000])

        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt,
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            result = response.choices[0].message.content
            return self._parse_response(result)
        except ConfigError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate post: {e}")
            return "CRYPTO", f"📰 {title}\n\n{content[:200]}..."

    @staticmethod
    def _parse_response(response: str) -> tuple[str, str]:
        base_asset = "CRYPTO"
        content = response

        for line in response.split("\n"):
            if line.startswith("BASE_ASSET:"):
                base_asset = line.split(":", 1)[1].strip()
            elif line.startswith("CONTENT:"):
                content = line.split(":", 1)[1].strip()

        return base_asset, content
