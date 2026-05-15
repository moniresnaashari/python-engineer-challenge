from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from whats_for_dinner.domain.exceptions import (
    RecipeError,
    RecipeGenerationError,
    RecipeNotFoundError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RecipeNotFoundError)
    async def recipe_not_found_handler(request: Request, exc: RecipeNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Recipe not found",
                "detail": str(exc),
            },
        )
    
    @app.exception_handler(RecipeGenerationError)
    async def recipe_generation_error_handler(request: Request, exc: RecipeGenerationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "Recipe generation failed",
                "detail": str(exc),
            },
        )
        
    @app.exception_handler(RecipeError)
    async def recipe_error_handler(request: Request, exc: RecipeError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Recipe error",
                "detail": str(exc),
            },
        )