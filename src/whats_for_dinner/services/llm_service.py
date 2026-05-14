from openai import AsyncOpenAI

from whats_for_dinner.core.config import settings
from whats_for_dinner.models.recipe import Recipe

client = AsyncOpenAI(
    api_key=settings.openai_api_key,
)


class LLMService:
    """Handles OpenAI interactions."""

    async def generate_recipe(
        self,
        ingredients: str,
        similar_recipes: list[Recipe],
    ) -> str:
        recipes_context = self._build_recipes_context(
            similar_recipes,
        )

        prompt = self._build_prompt(
            ingredients=ingredients,
            recipes_context=recipes_context,
        )

        response = await client.chat.completions.create(
            model="gpt-4o",
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional cooking assistant."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        content = response.choices[0].message.content

        if content is None:
            raise ValueError(
                "OpenAI returned empty recipe response"
            )

        return content

    def _build_prompt(
        self,
        ingredients: str,
        recipes_context: str,
    ) -> str:
        return f"""
Create a recipe recommendation based on the user's ingredients.

User ingredients:
{ingredients}

Reference recipes:
{recipes_context}

Requirements:
- Return Markdown formatted output
- Prefer ingredients explicitly provided by the user
- You may adapt ideas from the reference recipes
- If additional ingredients are needed,
  clearly mark them as optional
- Keep instructions concise and practical
- Include:
  - recipe title
  - ingredients
  - step-by-step instructions
- Do not invent unrealistic ingredients
"""

    def _build_recipes_context(
        self,
        recipes: list[Recipe],
    ) -> str:
        sections: list[str] = []

        for recipe in recipes:
            sections.append(
                f"""
Recipe:
{recipe.title}

Ingredients:
{recipe.ingredients}

Instructions:
{recipe.instructions}
"""
            )

        return "\n\n".join(sections)