import asyncio
import csv
import json
import uuid
import sys
import os
from datetime import datetime
from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import create_async_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.config import settings
from app.models import Base, DocumentModel


CSV_FILE_PATH = "data/posts.csv"

NAMESPACE_DOCUMENT = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

# Латинские омоглифы -> кириллица. В исходных данных токенизатору может быть сложно увидеь границы слова (из-за пересечения по буквам в русском и английском языках алгоритм разбивает не на правильные токены)
LATIN_TO_CYRILLIC = {
    "A": "а", "B": "в", "C": "с", "E": "е", "H": "н", "K": "к",
    "M": "м", "O": "о", "P": "р", "T": "т", "X": "х", "Y": "у",
    "a": "а", "c": "с", "e": "е", "o": "о", "p": "р", "x": "х", "y": "у",
}

# Служебные слова
RUSSIAN_FUNCTION_WORDS = [
    # предлоги
    "в", "во", "на", "с", "со", "об", "обо", "о", "от", "до",
    "для", "за", "из", "по", "про", "под", "над", "при",
    "без", "через", "около", "после", "перед", "между", "среди",
    "вокруг", "вдоль", "к", "ко", "у",
    # союзы
    "и", "или", "но", "а", "что", "если", "когда", "пока", "чем",
    "будто", "словно", "то",
    # частицы
    "не", "ни", "же", "бы", "ли", "ведь", "вот", "уж",
]

INDEX_SETTINGS = {
    "number_of_shards": 1,
    "number_of_replicas": 0,
    "analysis": {
        "char_filter": {
            "ru_yo": {
                "type": "mapping",
                "mappings": ["ё => е", "Ё => е"],
            },
            "ru_homoglyph": {
                "type": "mapping",
                "mappings": [
                    f"{latin} => {cyrillic}"
                    for latin, cyrillic in LATIN_TO_CYRILLIC.items()
                ],
            },
        },
        "filter": {
            "ru_stopwords": {
                "type": "stop",
                "stopwords": RUSSIAN_FUNCTION_WORDS,
                "ignore_case": True,
            },
            "ru_stemmer": {"type": "stemmer", "language": "russian"},
        },
        "analyzer": {
            "ru_text": {
                "type": "custom",
                "char_filter": ["ru_yo", "ru_homoglyph"],
                "tokenizer": "standard",
                "filter": ["lowercase", "ru_stopwords", "ru_stemmer"],
            }
        },
    },
}

async def init_databases():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    es = AsyncElasticsearch(settings.elastic_url)
    
    if await es.indices.exists(index=settings.ELASTIC_INDEX):
        await es.indices.delete(index=settings.ELASTIC_INDEX)
        
    await es.indices.create(
        index=settings.ELASTIC_INDEX,
        body={
            "settings": INDEX_SETTINGS,
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "text": {"type": "text", "analyzer": "ru_text"},
                }
            }
        }
    )
    
    print("Базы данных и индексы успешно инициализированы.")
    return engine, es

def parse_csv_file():
    documents = []
    if not os.path.exists(CSV_FILE_PATH):
        print(f"Критическая ошибка: Файл {CSV_FILE_PATH} не найден!")
        return documents

    with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=",", quotechar='"')
        
        for row in reader:
            try:
                text = row["text"].strip()
                created_date_str = row["created_date"].strip()
                rubrics_raw = row["rubrics"].strip()
                created_date = datetime.strptime(created_date_str, "%Y-%m-%d %H:%M:%S")
                rubrics_json = rubrics_raw.replace("'", '"')
                rubrics = json.loads(rubrics_json)
                unique_string = f"{text}_{created_date_str}"
                doc_id = str(uuid.uuid5(NAMESPACE_DOCUMENT, unique_string))
                
                documents.append({
                    "id": doc_id,
                    "text": text,
                    "created_date": created_date,
                    "rubrics": rubrics
                })
            except Exception as e:
                print(f"Ошибка парсинга строки CSV: {e}")
                continue
                
    return documents

async def main():
    await asyncio.sleep(2)
    
    engine, es = await init_databases()
    documents = parse_csv_file()
    
    if not documents:
        print("Нет данных для импорта.")
        await es.close()
        return

    print(f"Найдено {len(documents)} документов для импорта. Начинаем загрузку...")

    from sqlalchemy.ext.asyncio import AsyncSession
    async with AsyncSession(engine) as session:
        async with session.begin():
            db_objects = [
                DocumentModel(
                    id=doc["id"],
                    text=doc["text"],
                    created_date=doc["created_date"],
                    rubrics=doc["rubrics"]
                ) for doc in documents
            ]
            session.add_all(db_objects)
        await session.commit()

    bulk_body = []
    for doc in documents:
        bulk_body.append({"index": {"_index": settings.ELASTIC_INDEX, "_id": doc["id"]}})
        bulk_body.append({"id": doc["id"], "text": doc["text"]})
        
    if bulk_body:
        response = await es.bulk(operations=bulk_body)
        if response.get("errors"):
            print("Внимание: Произошли ошибки при индексации в Elasticsearch.")
        else:
            print(f"Успешно проиндексировано {len(documents)} документов в Elasticsearch.")

    await es.close()
    print("Импорт данных успешно завершен!")

if __name__ == "__main__":
    asyncio.run(main())
