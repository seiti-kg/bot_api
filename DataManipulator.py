from workalendar.america import Brazil
from datetime import datetime

class DataManipulator:
    def __init__(self, json_teste):
        self.json_teste = json_teste
        self.cal = Brazil()

    def get_dia_util(self, data_fornecida):
        data_obj = datetime.strptime(data_fornecida, "%d-%m-%Y").date()
        dia_util = self.cal.is_working_day(data_obj)
        if data_obj.weekday() == 5 or data_obj.weekday() == 6:
            return False
        if dia_util:
            return dia_util

    
    def passar_dia_util(self, data_fornecida):
        try:
            data_obj = data_fornecida.date()
            dia_util = self.cal.add_working_days(data_obj, -1)
            print(f"Próximo dia útil calculado: {dia_util}")  # Verifique a data calculada
            return dia_util
        except Exception as e:
            print(f"Erro ao passar dia útil: {e}")

    def autenticar_recesso(self, data_fornecida):
        dia_util = self.get_dia_util(data_fornecida) 
        
        if dia_util:
            print(f"{data_fornecida} é um dia útil!")
            return data_fornecida  
        else:
            dia_util_formatado = self.passar_dia_util(datetime.strptime(data_fornecida, "%d-%m-%Y"))
            if dia_util_formatado:
                print(f"{data_fornecida} não é dia útil, é um recesso ou ponto facultativo!")
                print(f"Próximo dia útil: {dia_util_formatado.strftime('%d-%m-%Y')}")
                return dia_util_formatado.strftime('%d-%m-%Y')  
            else:
                print("Erro ao encontrar o próximo dia útil.")
                return None


            
if __name__ == "__main__":
    manipulator = DataManipulator()
