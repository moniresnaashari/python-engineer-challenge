from contextlib import asynccontextmanager

from fastapi import FastAPI

from whats_for_dinner.api.exception_handlers import (
    register_exception_handlers,
)
from whats_for_dinner.api.recipes import (
    router as recipe_router,
)
from whats_for_dinner.core.database import (
    AsyncSessionLocal,
)
from whats_for_dinner.core.database import (
    create_database,
)
from whats_for_dinner.services.ingestion_service import (
    IngestionService,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_database()

    async with AsyncSessionLocal() as session:
        ingestion_service = IngestionService(
            session,
        )

        await ingestion_service.ingest_directory(
            "data/recipes",
        )

    yield


app = FastAPI(
    title="What's For Dinner API",
    lifespan=lifespan,
)

register_exception_handlers(app)

app.include_router(recipe_router)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}