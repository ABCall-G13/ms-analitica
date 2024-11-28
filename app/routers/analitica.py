from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import json
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.auth import default
import os

search_router = APIRouter()

# Modelo de datos para las solicitudes
class QueryRequest(BaseModel):
    query: str

SERVICE_ACCOUNT_FILE = "service-account.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

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

@search_router.post("/generate-response")
async def chat_with_gpt(query_request: QueryRequest):
    """Consulta la API de ChatGPT para obtener una respuesta generada por IA."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Cuerpo de la solicitud
    data = {
        "model": "gpt-4",  # Cambia a "gpt-3.5-turbo" si prefieres ese modelo
        "messages": [
            {"role": "system", "content": "Eres un asistente útil que ayuda a los usuarios a resolver problemas técnicos basado en problemas comunes existentes."},
            {"role": "user", "content": query_request.query}
        ],
        "temperature": 0.7,
        "max_tokens": 256,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

    try:
        # Realizar la solicitud a la API de OpenAI
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return {"response": result["choices"][0]["message"]["content"]}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar ChatGPT: {e}")
