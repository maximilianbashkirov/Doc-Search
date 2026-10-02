from typing import AsyncGenerator
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from elasticsearch import AsyncElasticsearch

from app.main import app
from app.config import settings
from app.database import get_db
from app.services.es_service import get_elastic



@pytest_asyncio.fixture(scope="session") # Тестовые сессии для СУБД и ES
async def test_engine():
    engine = create_async_engine(settings.database_url)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    AsyncSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(scope="session")
async def test_es() -> AsyncGenerator[AsyncElasticsearch, None]:
    es = AsyncElasticsearch(settings.elastic_url)
    yield es
    await es.close()

@pytest_asyncio.fixture(scope="function")
async def client(test_db, test_es) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_elastic] = lambda: test_es
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()
