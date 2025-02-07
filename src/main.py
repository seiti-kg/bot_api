from fastapi import FastAPI, APIRouter, HTTPException
from configuration import collection
from datetime import datetime
from database.models import Diario
from database.schemas import dados_individuais
from BotRetroactiveRead import DownloadRetroativo
from BotRetroactiveRead import DataManipulator


app = FastAPI()
router = APIRouter()

def converter_objectid_para_str(diario):
    if '_id' in diario:
        diario['_id'] = str(diario['_id'])
    return diario

@router.get("/diario")
async def pegar_todos_diarios():
    try:
        data = collection.find()
        data_lista = [converter_objectid_para_str(diario) for diario in data]
        return {"status_code": 200, "data": data_lista}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro ao buscar os diários: {str(e)}")

@router.post("/diario")
async def postar_diario(novoDiario: Diario):
    try:
        collection.insert_one(novoDiario.model_dump())
        return {"status_code": 200, "message": "Diário inserido com sucesso!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro: {e}")

app.include_router(router)

dataDeHoje = datetime.now()
json_teste = dataDeHoje.strftime("%d-%m-%Y")

if __name__ == "__main__":
    diario = DownloadRetroativo(json_teste)
    diario.acessar_site(json_teste)
    diario.executar()





