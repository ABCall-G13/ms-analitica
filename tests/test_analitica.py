import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.routers.analitica import search_router, QueryRequest

# Create an app instance and include the router
app = FastAPI()
app.include_router(search_router)

client = TestClient(app)

@pytest.fixture
def mock_service_account():
    with patch("app.routers.analitica.service_account.Credentials.from_service_account_file") as mock_cred:
        mock_credentials = MagicMock()
        mock_credentials.token = "mock_token"
        mock_cred.return_value = mock_credentials
        yield mock_cred

@pytest.fixture
def mock_request():
    with patch("app.routers.analitica.requests.post") as mock_request:
        yield mock_request

# Existing test cases
def test_search_success(mock_service_account, mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "id": "1",
                "document": {
                    "structData": {
                        "categoria": "Category 1",
                        "description": "Description 1",
                        "solucion": "Solution 1",
                        "cliente_id": "Client 1"
                    }
                }
            }
        ]
    }
    mock_request.return_value = mock_response
    response = client.post("/search-issues", json={"query": "sample query"})
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "1",
            "categoria": "Category 1",
            "description": "Description 1",
            "solucion": "Solution 1",
            "cliente_id": "Client 1"
        }
    ]

def test_search_no_results(mock_service_account, mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_request.return_value = mock_response
    response = client.post("/search-issues", json={"query": "non-existent query"})
    assert response.status_code == 404
    assert response.json() == {"detail": "No results found."}

def test_search_token_failure():
    with patch("app.routers.analitica.service_account.Credentials.from_service_account_file", side_effect=Exception("Token error")):
        response = client.post("/search-issues", json={"query": "sample query"})
        assert response.status_code == 500
        assert response.json() == {"detail": "Failed to obtain access token: Token error"}

def test_search_api_failure(mock_service_account, mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    mock_request.return_value = mock_response
    response = client.post("/search-issues", json={"query": "sample query"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Service Unavailable"}

# Additional test cases for increased coverage
def test_search_missing_query_field(mock_service_account, mock_request):
    response = client.post("/search-issues", json={})
    assert response.status_code == 422  # Unprocessable Entity (FastAPI validation error)

def test_search_invalid_query_field_type(mock_service_account, mock_request):
    response = client.post("/search-issues", json={"query": 12345})
    assert response.status_code == 422  # Unprocessable Entity (FastAPI validation error)

def test_search_invalid_credentials(mock_service_account, mock_request):
    with patch("app.routers.analitica.service_account.Credentials.from_service_account_file", side_effect=Exception("Invalid credentials")):
        response = client.post("/search-issues", json={"query": "sample query"})
        assert response.status_code == 500
        assert response.json() == {"detail": "Failed to obtain access token: Invalid credentials"}

def test_search_forbidden_response(mock_service_account, mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"
    mock_request.return_value = mock_response
    response = client.post("/search-issues", json={"query": "sample query"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}

def test_search_internal_server_error(mock_service_account, mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_request.return_value = mock_response
    response = client.post("/search-issues", json={"query": "sample query"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}

def test_chat_with_gpt_success(mock_request):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "This is a generated response."
                }
            }
        ]
    }
    mock_request.return_value = mock_response
    response = client.post("/generate-response", json={"query": "sample query"})
    assert response.status_code == 200
    assert response.json() == {"response": "This is a generated response."}

def test_chat_with_gpt_invalid_query_field_type(mock_request):
    response = client.post("/generate-response", json={"query": 12345})
    assert response.status_code == 422  # Unprocessable Entity (FastAPI validation error)

def test_chat_with_gpt_missing_query_field(mock_request):
    response = client.post("/generate-response", json={})
    assert response.status_code == 422  # Unprocessable Entity (FastAPI validation error)
