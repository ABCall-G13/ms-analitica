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

def test_search_success(mock_service_account, mock_request):
    # Mock response data
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
            },
            # Additional mock results as needed
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
        # Additional expected results
    ]

def test_search_no_results(mock_service_account, mock_request):
    # Mock a 200 response with no results
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_request.return_value = mock_response

    response = client.post("/search-issues", json={"query": "non-existent query"})

    assert response.status_code == 404
    assert response.json() == {"detail": "No results found."}

def test_search_token_failure():
    # Mock failure in retrieving the access token
    with patch("app.routers.analitica.service_account.Credentials.from_service_account_file", side_effect=Exception("Token error")):
        response = client.post("/search-issues", json={"query": "sample query"})
        assert response.status_code == 500
        assert response.json() == {"detail": "Failed to obtain access token: Token error"}

def test_search_api_failure(mock_service_account, mock_request):
    # Mock an API failure response
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    mock_request.return_value = mock_response

    response = client.post("/search-issues", json={"query": "sample query"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Service Unavailable"}
