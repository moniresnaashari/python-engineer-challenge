import pytest

from whats_for_dinner.services.recipe_service import RecipeService


@pytest.mark.anyio
async def test_build_recipe_context() -> None:
    service = RecipeService(session=None)  # type: ignore

    context = service._build_recipe_context([])

    assert context == ""