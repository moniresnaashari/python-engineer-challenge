from openai import AsyncOpenAI

from whats_for_dinner.core.config import settings

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def create_embedding(text: str) -> list[float]:
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )

    return response.data[0].embedding