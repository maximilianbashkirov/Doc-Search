from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from elasticsearch import AsyncElasticsearch, NotFoundError
from typing import List

from app.database import get_db
from app.services.es_service import get_elastic
from app.models import DocumentModel
from app.schemas import DocumentResponse
from app.config import settings

app = FastAPI(
    title="Search Service",
    description="Асинхронный сервис поиска документов",
    version="1.0.0"
)

@app.get(
    "/search", 
    response_model=List[DocumentResponse], 
    summary="Полнотекстовый поиск документов"
)
async def search_documents(
    query: str = Query(..., min_length=1, description="Поисковый запрос"),
    db: AsyncSession = Depends(get_db),
    es: AsyncElasticsearch = Depends(get_elastic)
):
    try:
        # Ищем совпадения в Elasticsearch
        es_response = await es.search(
            index=settings.ELASTIC_INDEX,
            query={"match": {"text": query}},
            size=1000,
            source=["id"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка Elasticsearch: {str(e)}"
        )

    hits = es_response.get("hits", {}).get("hits", [])
    if not hits:
        return []

    document_ids = [hit["_source"]["id"] for hit in hits]

    # Запрос в PostgreSQL с сортировкой по убыванию даты и лимитом в 20 записей
    stmt = (
        select(DocumentModel)
        .where(DocumentModel.id.in_(document_ids))
        .order_by(DocumentModel.created_date.desc())
        .limit(20)
    )
    
    result = await db.execute(stmt)
    documents = result.scalars().all()
    return documents

@app.delete(
    "/document/{id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление документа"
)
async def delete_document(
    id: str,
    db: AsyncSession = Depends(get_db),
    es: AsyncElasticsearch = Depends(get_elastic)
):
    stmt = select(DocumentModel).where(DocumentModel.id == id)
    result = await db.execute(stmt)
    db_document = result.scalar_one_or_none()

    if not db_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Документ с ID {id} не найден."
        )

    await db.delete(db_document)
    await db.commit()

    try:
        await es.delete(index=settings.ELASTIC_INDEX, id=id)
    except NotFoundError:
        pass
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка удаления из Elasticsearch: {str(e)}"
        )

    return None
