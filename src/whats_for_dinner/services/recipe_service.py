from sqlalchemy.ext.asyncio import AsyncSession

from whats_for_dinner.repositories.recipe_repository import (
    RecipeRepository,
)
from whats_for_dinner.pipelines.rag_pipeline import get_rag_pipeline
from whats_for_dinner.domain.exceptions import (
    RecipeGenerationError,
    RecipeNotFoundError,
)


class RecipeService:
    """Recipe recommendation business logic."""

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.repository = RecipeRepository(session)
        self.rag_pipeline = get_rag_pipeline()

    async def recommend_recipe(
        self,
        ingredients: str,
        extracted_ingredients: str | None = None,
    ) -> str:
        if not ingredients.strip() and not extracted_ingredients:
            raise RecipeGenerationError("No ingredients provided")
            
        # Combine text ingredients with extracted ingredients from image
        combined_ingredients = self._combine_ingredients(
            ingredients, 
            extracted_ingredients
        )
        
        # Ensure pipeline has recipes loaded
        await self._ensure_recipes_loaded()
        
        try:
            # Use Haystack pipeline for RAG
            result = await self.rag_pipeline.recommend_recipe(combined_ingredients)
            if not result or not result.strip():
                raise RecipeGenerationError("Failed to generate recipe recommendation")
            return result
        except Exception as e:
            raise RecipeGenerationError(f"Recipe generation failed: {str(e)}") from e
    
    def _combine_ingredients(
        self,
        text_ingredients: str,
        extracted_ingredients: str | None,
    ) -> str:
        """Combine text ingredients with extracted ingredients from image."""
        if not text_ingredients.strip():
            return extracted_ingredients
            
        return f"{text_ingredients}\n\nAdditionally found in image:\n{extracted_ingredients}"
    
    async def _ensure_recipes_loaded(self) -> None:
        """Ensure recipes are loaded in the RAG pipeline."""
        if not self.rag_pipeline.are_recipes_loaded():
            # Get all recipes from database
            all_recipes = await self.repository.get_all_recipes()
            if not all_recipes:
                raise RecipeNotFoundError("No recipes found in database")
            await self.rag_pipeline.load_recipes(all_recipes)