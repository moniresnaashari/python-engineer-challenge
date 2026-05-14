from fastapi import APIRouter
from fastapi import Depends
from fastapi import Form
from fastapi import File
from fastapi import UploadFile
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from whats_for_dinner.core.database import get_session
from whats_for_dinner.domain.schemas import RecommendRecipeResponse
from whats_for_dinner.custom_components import ExtractFoodItemsFromImage
from whats_for_dinner.services.recipe_service import RecipeService

router = APIRouter()


@router.post(
    "/recommend_recipe",
    response_model=RecommendRecipeResponse,
)
async def recommend_recipe(
    ingredients: str = Form(...),
    image: UploadFile | None = File(None),
    session: AsyncSession = Depends(get_session),
) -> RecommendRecipeResponse:
    """
    Generate recipe recommendations from ingredients with optional image upload.
    
    Form data parameters:
    - ingredients: Text description of available ingredients (required)
    - image: Optional image file containing ingredients to analyze
    
    The image will be analyzed to extract visible ingredients if provided.
    """
    
    service = RecipeService(session)
    extracted_ingredients = None
    
    # Process image if provided
    if image is not None:
        # Validate image file
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Uploaded file must be an image")
            
        # Use Haystack custom component
        extractor = ExtractFoodItemsFromImage()
        result = await extractor.run(image_file=image)
        extracted_ingredients = result["answer"]

    recipe = await service.recommend_recipe(
        ingredients=ingredients,
        extracted_ingredients=extracted_ingredients,
    )

    return RecommendRecipeResponse(recipe=recipe)