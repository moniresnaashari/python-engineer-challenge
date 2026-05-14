from sqlalchemy.ext.asyncio import AsyncSession

from whats_for_dinner.repositories.recipe_repository import (
    RecipeRepository,
)
from whats_for_dinner.services.embedding_service import (
    create_embedding,
)
from whats_for_dinner.services.llm_service import (
    LLMService,
)


class RecipeService:
    """Recipe recommendation business logic."""

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.repository = RecipeRepository(session)
        self.llm_service = LLMService()

    async def recommend_recipe(
        self,
        ingredients: str,
        extracted_ingredients: str | None = None,
    ) -> str:
        # Combine text ingredients with extracted ingredients from image
        combined_ingredients = self._combine_ingredients(
            ingredients, 
            extracted_ingredients
        )
        
        embedding = await create_embedding(
            combined_ingredients,
        )

        similar_recipes = (
            await self.repository.find_similar_recipes(
                embedding=embedding,
            )
        )

        return await self.llm_service.generate_recipe(
            ingredients=combined_ingredients,
            similar_recipes=similar_recipes,
        )
    
    def _combine_ingredients(
        self,
        text_ingredients: str,
        extracted_ingredients: str | None,
    ) -> str:
        """Combine text ingredients with extracted ingredients from image."""
        if not text_ingredients.strip():
            return extracted_ingredients
            
        return f"{text_ingredients}\n\nAdditionally found in image:\n{extracted_ingredients}"