from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)


class ContentGenerator:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    async def generate_post(self, title: str, content: str) -> tuple[str, str]:
        prompt = f"""请将以下新闻改写为适合社交媒体发布的贴文格式：

要求：
1. 简洁有力，吸引眼球
2. 在开头明确指出主要涉及的加密货币（格式：$BTC $ETH 等），如果有多个最多3个
3. 长度控制在200字以内
4. 语气专业但不失活泼
5. 可以适当的添加一些emoji让内容更生动

新闻标题：{title}
新闻内容：{content[:1000]}

请按以下格式返回：
BASE_ASSET: BTC
CONTENT: 这里是贴文内容..."""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的加密货币新闻编辑，擅长将新闻改写为社交媒体贴文。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            return self._parse_response(result)
        except Exception as e:
            logger.error(f"Failed to generate post: {e}")
            return "CRYPTO", f"📰 {title}\n\n{content[:200]}..."
    
    def _parse_response(self, response: str) -> tuple[str, str]:
        base_asset = "CRYPTO"
        content = response
        
        for line in response.split("\n"):
            if line.startswith("BASE_ASSET:"):
                base_asset = line.split(":", 1)[1].strip()
            elif line.startswith("CONTENT:"):
                content = line.split(":", 1)[1].strip()
        
        return base_asset, content
