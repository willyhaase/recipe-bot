import httpx
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ти дружній досвідчений шеф-кухар та кулінарний порадник.
Відповідай на питання про їжу та кулінарію виключно українською мовою.
Коли пропонуєш рецепт — давай короткий список інгредієнтів та основні кроки приготування.
Будь практичним: враховуй час, доступність продуктів, рівень складності.
Якщо користувач запитує щось не пов'язане з їжею — ввічливо поверни розмову до кулінарної теми.
Відповідай лаконічно, використовуй емодзі для наочності."""


class ClaudeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def ask_chef(self, question: str) -> str:
        """Ask the AI chef a culinary question."""
        try:
            resp = await self.client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1024,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": question}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return "😔 Не вдалося отримати відповідь від AI-шефа. Спробуй пізніше."
