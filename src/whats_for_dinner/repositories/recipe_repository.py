from sqlalchemy import bindparam
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.types import Float

from whats_for_dinner.models.recipe import Recipe


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

    async def find_similar_recipes(
        self,
        embedding: list[float],
        limit: int = 3,
    ) -> list[Recipe]:
        statement = (
            text("""
                SELECT
                    id,
                    title,
                    ingredients,
                    instructions
                FROM recipes
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
            """)
            .bindparams(
                bindparam(
                    "embedding",
                    type_=ARRAY(Float),
                ),
            )
        )

        result = await self.session.execute(
            statement,
            {
                "embedding": embedding,
                "limit": limit,
            },
        )

        rows = result.mappings().all()

        recipes: list[Recipe] = []

        for row in rows:
            recipes.append(
                Recipe(
                    id=row["id"],
                    title=row["title"],
                    ingredients=row["ingredients"],
                    instructions=row["instructions"],
                    embedding=[],
                )
            )

        return recipes