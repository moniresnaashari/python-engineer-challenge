from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from whats_for_dinner.models.recipe import Recipe
from whats_for_dinner.domain.exceptions import RecipeNotFoundError


class RecipeRepository:
    """Database operations related to recipes."""

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create_recipe(
        self,
        recipe: Recipe,
    ) -> None:
        self.session.add(recipe)

    async def commit(self) -> None:
        await self.session.commit()

    async def exists(self) -> bool:
        result = await self.session.execute(
            select(Recipe.id).limit(1)
        )

        return result.first() is not None

    
    async def get_all_recipes(self) -> list[Recipe]:
        """Get all recipes from the database."""
        try:
            result = await self.session.execute(
                select(Recipe)
            )
            
            recipes = list(result.scalars().all())
            if not recipes:
                raise RecipeNotFoundError("No recipes found in database")
            
            return recipes
        except Exception as e:
            if isinstance(e, RecipeNotFoundError):
                raise
            raise RecipeNotFoundError(f"Failed to retrieve recipes: {str(e)}") from e