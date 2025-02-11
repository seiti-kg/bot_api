from pydantic import BaseModel
from typing import List

class Caderno(BaseModel):
    caderno: str
    status_leitura: bool
    caminho_arquivo: str

class Diario(BaseModel):
    data_diario: str
    tribunal: str
    cadernos: List[Caderno]


