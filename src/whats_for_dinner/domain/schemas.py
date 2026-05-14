from pydantic import BaseModel


class RecommendRecipeRequest(BaseModel):
    ingredients: str


class RecommendRecipeResponse(BaseModel):
    recipe: str


class RecommendRecipeFormData(BaseModel):
    ingredients: str
    extracted_ingredients: str | None = None