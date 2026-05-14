from fastapi import FastAPI
from fastapi.responses import JSONResponse

from whats_for_dinner.domain.exceptions import RecipeError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RecipeError)
    async def recipe_error_handler(_, exc: RecipeError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": str(exc),
            },
        )