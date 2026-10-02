import pytest
from fastapi import status

@pytest.mark.asyncio
async def test_search_endpoint_success(client):
    response = await client.get("/search", params={"query": "Условия"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    
    if len(data) > 1:
        assert data[0]["created_date"] >= data[1]["created_date"]

@pytest.mark.asyncio
async def test_search_no_results(client):
    response = await client.get("/search", params={"query": "non_existent_text_matching_nothing"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

@pytest.mark.asyncio
async def test_search_validation_error(client):
    response = await client.get("/search", params={"query": ""})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# падежи
@pytest.mark.asyncio
async def test_search_russian_morphology(client):
    response = await client.get("/search", params={"query": "заказов"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) > 0

# омоглифы
@pytest.mark.asyncio
async def test_search_latin_homoglyphs(client):
    response = await client.get("/search", params={"query": "пловцов"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) > 0


@pytest.mark.asyncio
async def test_delete_document_flow(client):
    search_response = await client.get("/search", params={"query": "Условия"})
    assert search_response.status_code == status.HTTP_200_OK
    search_data = search_response.json()
    
    if not search_data:
        pytest.skip("Нет данных")
        
    target_id = search_data[0]["id"]
    
    # DELETE запрос
    delete_response = await client.delete(f"/document/{target_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    
    # 404 статус
    retry_delete = await client.delete(f"/document/{target_id}")
    assert retry_delete.status_code == status.HTTP_404_NOT_FOUND
