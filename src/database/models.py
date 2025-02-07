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

    def inserir(self, Caderno):
        self.cadernos.append(Caderno)
        print(f"Diário salvo: {Caderno}")


class BancoDeDadosFalso:
    def __init__(self):
        self.diarios = []  

    def inserir(self, diario):
        self.diarios.append(diario)
        print(f"Diário salvo: {diario}")

    def listar_diarios(self):
        if self.diarios:
            print("Diários salvos:")
            for diario in self.diarios:
                print(diario)
        else:
            print("Nenhum diário encontrado.")
