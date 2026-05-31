import httpx
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://api.spoonacular.com"


class SpoonacularClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=15.0)

    def _params(self, **kwargs) -> dict:
        return {"apiKey": self.api_key, **kwargs}

    async def search_by_ingredients(self, ingredients: str, number: int = 8) -> list[dict]:
        """Search recipes by comma-separated ingredients."""
        try:
            resp = await self.client.get(
                f"{BASE_URL}/recipes/findByIngredients",
                params=self._params(
                    ingredients=ingredients,
                    number=number,
                    ranking=1,
                    ignorePantry=True,
                ),
            )
            resp.raise_for_status()
            data = resp.json()
            return [{"id": r["id"], "title": r["title"], "image": r.get("image", "")} for r in data]
        except Exception as e:
            logger.error(f"search_by_ingredients error: {e}")
            return []

    async def search_by_name(self, query: str, number: int = 8) -> list[dict]:
        """Search recipes by dish name."""
        try:
            resp = await self.client.get(
                f"{BASE_URL}/recipes/complexSearch",
                params=self._params(
                    query=query,
                    number=number,
                    addRecipeInformation=False,
                ),
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            return [{"id": r["id"], "title": r["title"], "image": r.get("image", "")} for r in results]
        except Exception as e:
            logger.error(f"search_by_name error: {e}")
            return []

    async def search_by_category(self, meal_type: str, number: int = 8) -> list[dict]:
        """Search recipes by meal type / category."""
        try:
            resp = await self.client.get(
                f"{BASE_URL}/recipes/complexSearch",
                params=self._params(
                    type=meal_type,
                    number=number,
                    sort="popularity",
                ),
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            return [{"id": r["id"], "title": r["title"], "image": r.get("image", "")} for r in results]
        except Exception as e:
            logger.error(f"search_by_category error: {e}")
            return []

    async def get_recipe_details(self, recipe_id: int) -> dict | None:
        """Fetch full recipe details including ingredients and instructions."""
        try:
            resp = await self.client.get(
                f"{BASE_URL}/recipes/{recipe_id}/information",
                params=self._params(includeNutrition=False),
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"get_recipe_details error: {e}")
            return None
