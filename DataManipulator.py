from workalendar.america import Brazil
from datetime import date
from BotRetroactiveRead import DownloadRetroativo

class DataManipulator:
    def __init__(self):
        self.cal = Brazil()

    def get_dia_util(self, data_fornecida):
        data_fornecida = DownloadRetroativo.get_data_formatada()
        dia_util = self.cal.get_working_day(data_fornecida)
        if dia_util:
            return dia_util
        else:
            return self.passar_dia_util(data_fornecida)
    
    def passar_dia_util(self, data_fornecida):
        data_fornecida = DownloadRetroativo.get_data_formatada()
        try:
            dia_util = self.cal.get_working_day(data_fornecida, 1)
            return dia_util
        except Exception as e:
            print(f"Erro ao passar dia útil: {e}")
            
if __name__ == "__main__":
    manipulator = DataManipulator()
