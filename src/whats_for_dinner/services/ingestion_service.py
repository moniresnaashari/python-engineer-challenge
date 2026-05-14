import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from whats_for_dinner.models.recipe import Recipe
from whats_for_dinner.repositories.recipe_repository import (
    RecipeRepository,
)
from whats_for_dinner.services.embedding_service import (
    create_embedding,
)

logger = logging.getLogger(__name__)


class IngestionService:
    """Imports recipe text files into Postgres."""

    def __init__(self, session: AsyncSession) -> None:
        self.repository = RecipeRepository(session)

    async def ingest_directory(
        self,
        directory_path: str,
    ) -> None:
        already_ingested = await self.repository.exists()

        if already_ingested:
            logger.info("Recipes already ingested")
            return

        recipe_files = sorted(
            Path(directory_path).glob("*.txt")
        )

        for recipe_file in recipe_files:
            recipe = await self._parse_recipe_file(
                recipe_file,
            )

            await self.repository.create_recipe(
                recipe,
            )

        # Single commit for better performance
        await self.repository.commit()

        logger.info(
            "Recipe ingestion completed",
            extra={
                "count": len(recipe_files),
            },
        )

    async def _parse_recipe_file(
        self,
        file_path: Path,
    ) -> Recipe:
        content = file_path.read_text(
            encoding="utf-8",
        )

        # Normalize line endings because datasets
        # may contain Windows-style newlines
        content = content.replace(
            "\r\n",
            "\n",
        )

        (
            title,
            ingredients,
            instructions,
        ) = self._extract_recipe_sections(
            content,
        )

        searchable_text = self._build_searchable_text(
            title=title,
            ingredients=ingredients,
        )

        embedding = await create_embedding(
            searchable_text,
        )

        return Recipe(
            title=title,
            ingredients=ingredients,
            instructions=instructions,
            embedding=embedding,
        )

    def _extract_recipe_sections(
        self,
        content: str,
    ) -> tuple[str, str, str]:
        ingredients_marker = "Ingredients:"
        instructions_marker = "Instructions:"

        ingredients_index = content.find(
            ingredients_marker,
        )

        instructions_index = content.find(
            instructions_marker,
        )

        if ingredients_index == -1:
            raise ValueError(
                "Recipe file missing Ingredients section"
            )

        if instructions_index == -1:
            raise ValueError(
                "Recipe file missing Instructions section"
            )

        title = content[
            :ingredients_index
        ].strip()

        ingredients = content[
            ingredients_index + len(ingredients_marker):
            instructions_index
        ].strip()

        instructions = content[
            instructions_index + len(instructions_marker):
        ].strip()

        return (
            title,
            ingredients,
            instructions,
        )

    def _build_searchable_text(
        self,
        title: str,
        ingredients: str,
    ) -> str:
        return f"""
Title:
{title}

Ingredients:
{ingredients}
"""