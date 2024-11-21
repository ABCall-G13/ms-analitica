from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import json
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import os

search_router = APIRouter()

class QueryRequest(BaseModel):
    query: str

SERVICE_ACCOUNT_FILE = "service-account.json"

@search_router.post("/search-issues")
async def search(query_request: QueryRequest):
    try:
        if os.getenv("ENV") == "production":
            credentials, project_id = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        else:
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            
        
        credentials.refresh(Request())
        access_token = credentials.token
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to obtain access token: {e}")

    url = "https://discoveryengine.googleapis.com/v1alpha/projects/345518488840/locations/global/collections/default_collection/engines/abcall-search-issues_1731299780547/servingConfigs/default_search:search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    data = {
        "query": query_request.query,
        "pageSize": 10,
        "queryExpansionSpec": {"condition": "AUTO"},
        "spellCorrectionSpec": {"mode": "AUTO"}
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        result = response.json().get("results", [])
        if result:
            top_results = result[:5]
            formatted_results = [
                {
                    "id": res.get("id"),
                    "categoria": res["document"]["structData"].get("categoria"),
                    "description": res["document"]["structData"].get("description"),
                    "solucion": res["document"]["structData"].get("solucion"),
                    "cliente_id": res["document"]["structData"].get("cliente_id")
                }
                for res in top_results
            ]
            return formatted_results
        else:
            raise HTTPException(status_code=404, detail="No results found.")
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)
