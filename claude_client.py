import httpx
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_CHEF = """Ти дружній досвідчений шеф-кухар та кулінарний порадник.
Відповідай на питання про їжу та кулінарію виключно українською мовою.
Коли пропонуєш рецепт - давай короткий список інгредієнтів та основні кроки приготування.
Будь практичним: враховуй час, доступність продуктів, рівень складності.
Якщо користувач запитує щось не пов'язане з їжею - ввічливо поверни розмову до кулінарної теми.
Відповідай лаконічно, використовуй емодзі для наочності."""

SYSTEM_PROMPT_TRANSLATE = """Ти перекладач кулінарних рецептів.
Переклади наданий текст рецепту з англійської на українську мову.
Зберігай оригінальну структуру та форматування (зірочки, дужки, тире, переноси рядків).
Назви інгредієнтів перекладай природно - використовуй загальноприйняті українські назви.
Повертай ТІЛЬКИ перекладений текст, без пояснень та коментарів."""

SYSTEM_PROMPT_TITLES = """Ти перекладач назв страв.
Тобі надається список назв страв англійською мовою - кожна з нового рядка.
Переклади кожну назву на українську мову.
Повертай ТІЛЬКИ переклади у тому самому порядку, кожен з нового рядка, без нумерації та пояснень."""

SYSTEM_PROMPT_QUERY = """Ти перекладач кулінарних запитів.
Переклади наданий запит або список інгредієнтів з української на англійську.
Якщо це список інгредієнтів - переклади кожен через кому.
Якщо це назва страви - переклади назву.
Повертай ТІЛЬКИ англійський переклад, без пояснень та коментарів."""


class ClaudeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    async def _call(self, system: str, user: str, max_tokens: int = 1024) -> str:
        resp = await self.client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-5",
                "max_tokens": max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        if resp.status_code != 200:
            logger.error(f"Anthropic API error {resp.status_code}: {resp.text}")
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    async def ask_chef(self, question: str) -> str:
        try:
            return await self._call(SYSTEM_PROMPT_CHEF, question)
        except Exception as e:
            logger.error(f"Claude chef error: {e}")
            return "😔 Не вдалося отримати відповідь від AI-шефа. Спробуй пізніше."

    async def translate_recipe(self, text: str) -> str:
        try:
            return await self._call(SYSTEM_PROMPT_TRANSLATE, text, max_tokens=2048)
        except Exception as e:
            logger.error(f"Claude translate_recipe error: {e}")
            return text

    async def translate_titles(self, recipes: list) -> list:
        try:
            titles = "\n".join(r["title"] for r in recipes)
            translated = await self._call(SYSTEM_PROMPT_TITLES, titles, max_tokens=512)
            translated_list = [t.strip() for t in translated.strip().split("\n") if t.strip()]
            if len(translated_list) == len(recipes):
                for i, r in enumerate(recipes):
                    r["title"] = translated_list[i]
            return recipes
        except Exception as e:
            logger.error(f"Claude translate_titles error: {e}")
            return recipes

    async def translate_query(self, text: str) -> str:
        try:
            result = await self._call(SYSTEM_PROMPT_QUERY, text, max_tokens=256)
            logger.info(f"translate_query success: '{text}' -> '{result}'")
            return result
        except Exception as e:
            logger.error(f"Claude query translate error: {type(e).__name__}: {e}")
            return text
