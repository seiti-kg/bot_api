from fastapi import FastAPI, APIRouter, HTTPException
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from typing import List
from datetime import datetime
from .database.models import Diario
from .database.schemas import dados_individuais
from .BotRetroactiveRead import DownloadRetroativo

import threading
import uvicorn

uri = "mongodb://mongo:27017/"

client = MongoClient(uri, server_api=ServerApi('1'))
db = client['diario_db']
collection = db['diario_data']


app = FastAPI()
router = APIRouter()

def start_download_retroativo():
    dataDeHoje = datetime.now()
    json_teste = dataDeHoje.strftime("%d-%m-%Y")
    diario = DownloadRetroativo(json_teste)
    diario.acessar_site(json_teste)
    diario.executar()


def converter_objectid_para_str(diario):
    if '_id' in diario:
        diario['_id'] = str(diario['_id'])
    return diario

@router.get("/diario", response_model=List[Diario])
async def pegar_todos_diarios():
    try:
        diarios = list(collection.find())
        return [Diario(**converter_objectid_para_str(diario)) for diario in diarios]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar diários: {str(e)}")

@router.post("/diario", response_model=Diario)
async def postar_diario(novo_diario: Diario):
    try:
        diario_dict = novo_diario.model_dump()
        resultado = collection.insert_one(diario_dict)
        diario_inserido = collection.find_one({"_id": resultado.inserted_id})
        return Diario(**converter_objectid_para_str(diario_inserido))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao inserir diário: {str(e)}")
    
app.include_router(router)

@app.on_event("startup")
def startup_event():
    download_thread = threading.Thread(target=start_download_retroativo)
    download_thread.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)





