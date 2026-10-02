from typing import AsyncGenerator
from elasticsearch import AsyncElasticsearch
from app.config import settings

async def get_elastic() -> AsyncGenerator[AsyncElasticsearch, None]:
    async with AsyncElasticsearch(settings.elastic_url) as client:
        yield client
