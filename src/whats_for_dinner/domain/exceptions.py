class RecipeError(Exception):
    pass


class RecipeGenerationError(RecipeError):
    pass


class RecipeNotFoundError(RecipeError):
    pass