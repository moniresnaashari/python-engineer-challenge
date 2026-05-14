from pydantic import BaseModel


class RecommendRecipeResponse(BaseModel):
    recipe: str