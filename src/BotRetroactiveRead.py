from selenium import webdriver;
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from DataManipulator import DataManipulator
from database.models import BancoDeDadosFalso

from pydantic import BaseModel
from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from configuration import collection
from database.models import Diario


from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter
 
import requests
import easyocr as eocr
import locale
import numpy as np
import time
import json
import os
import re


class DownloadRetroativo:
    def __init__(self, json_teste):
        self.banco_falso = BancoDeDadosFalso()
        self.download_dir = os.path.join(os.getcwd(), "TJMG")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        self.chrome_options = Options()
        self.chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
            "safebrowsing.enabled": "false"
        })

        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=self.chrome_options)

        self.json_teste = json_teste
        self.data_formatada = self.get_data_formatada()
        self.dia_util_formatado = json_teste

        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

    def get_data_formatada(self):
        data_hoje = datetime.now().strftime("%d de %B de %Y")
        data_hoje_dt = datetime.strptime(data_hoje, "%d de %B de %Y")
        data_formatada = data_hoje_dt.strftime("%d de %B de %Y")
        return data_formatada.replace(data_formatada.split()[2], data_formatada.split()[2].capitalize())

    def slp(self, seconds):
        time.sleep(seconds)
      
    def preprocess_image(self, image_path):
        img = Image.open(image_path)
        
        width, height = img.size
        new_width = int(width * 1.5)  
        new_height = int(height * 1.5)  
        img = img.resize((new_width, new_height), Image.LANCZOS) 
        contrast = ImageEnhance.Contrast(img)
        sharpness = ImageEnhance.Sharpness(img)
        img = img.filter(ImageFilter.SMOOTH)
        img = contrast.enhance(4.0)
        img = sharpness.enhance(4.0)
        img_rgb = img.convert('RGB')
        np_img = np.array(img_rgb)
        red_mask = (np_img[:, :, 0] >= 100) & (np_img[:, :, 1] <= 100) & (np_img[:, :, 2] <= 100)
        np_img[~red_mask] = 150 
        img_red = Image.fromarray(np_img)
        preprocessed_image_path = 'preprocessed_captcha.png'
        img_red.save(preprocessed_image_path)
        
        return img_red


    def monitorar_download(self, nome_arquivo_base):
        tentativas = 0
        while tentativas < 3:
            arquivos = os.listdir(self.download_dir)
            for arquivo in arquivos:
                if arquivo.startswith(nome_arquivo_base) and arquivo.endswith('.crdownload'):
                    while arquivo.endswith('.crdownload'):
                        self.slp(1)
                        arquivos = os.listdir(self.download_dir)
                        for arquivo_atualizado in arquivos:
                            if arquivo_atualizado.startswith(nome_arquivo_base) and arquivo_atualizado.endswith('.PDF'):
                                arquivo = arquivo_atualizado
                    return True
                elif arquivo.startswith(nome_arquivo_base) and not arquivo.endswith('.crdownload'):
                    return True
            self.slp(1)
            tentativas += 1
        return False

    def gerar_nome_arquivo(self, data):
        data_obj = datetime.strptime(data, "%d-%m-%Y")
        return f"SI{data_obj.strftime('%Y%m%d')}.PDF"
    
    def buscar_diario(self):
        opcoes_data = self.driver.find_elements(By.XPATH, "/html/body/div[2]/table/tbody/tr/td/table/tbody/tr")
        data_encontrada = False
        for opcao in opcoes_data:
            try:
                data_texto = opcao.find_element(By.XPATH, ".//td/li/a").text.strip()
                print(data_texto)
                if data_texto == self.data_formatada:
                    print("Data encontrada!")
                    data_encontrada = True
                    opcao_link = opcao.find_element(By.XPATH, ".//td/li/a")
                    WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(opcao_link)
                    )
                    opcao_link.click()
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    break     
            except Exception as e:
                print(e)
        if not data_encontrada:
            print("Data não encontrada")
            return False
        return True

    def captchaSolver(self):
        try:
            captcha_element = WebDriverWait(self.driver, 10).until(
                EC.visibility_of_element_located((By.ID, "captcha_image"))
            )

            with open('captcha.png', 'wb') as file:
                file.write(captcha_element.screenshot_as_png)
            print("Captcha capturado com sucesso!")
        except Exception as e:
            print(f"Erro ao capturar CAPTCHA: `{e}")

        self.slp(2)

        image_path = 'captcha.png'
        preprocessed_image = self.preprocess_image(image_path)
        reader = eocr.Reader(['en'])
        result = reader.readtext(np.array(preprocessed_image))

        captcha_text = ""
        for detection in result:
            text = detection[1]
            numbers = re.findall(r'\d+', text)
            for number in numbers:
                if len(number) <= 5:
                    captcha_text = number
                    break

        print("Texto do CAPTCHA:", captcha_text)

        captcha_box = self.driver.find_element(By.ID, "captcha_text")
        captcha_box.click()
        captcha_box.send_keys(captcha_text)
        captcha_box.send_keys(Keys.RETURN)
        print("Captcha enviado!")

        self.slp(2)

    def acessar_site(self, data_para_enviar):
        self.driver.get("https://www.tjmg.jus.br/portal-tjmg/")
        self.driver.maximize_window()
        self.slp(3)

        caminho_diarios = self.driver.find_element(By.XPATH, '//*[@id="submenu"]/div/div/div[1]/div/div/div/a')
        self.driver.execute_script("arguments[0].click();", caminho_diarios)

        self.slp(1)
        try:
            cookies = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "termo-uso-btn"))
            )
            cookies.click()
        except TimeoutException:
            pass
        
        finally:
            caminho_dje = self.driver.find_element(By.XPATH, '//*//div[@class=\'introduction\'][contains(text(),\'Diário do Judiciário eletrônico do Tribunal de Justiça de MG\')]')
            caminho_dje.click()
            self.slp(1)

            edicoes_anteriores = self.driver.find_element(By.LINK_TEXT, "Edições Anteriores")
            edicoes_anteriores.click()

            escolha = self.driver.find_element(By.ID, "tipoDiario")
            escolha.click()

            self.slp(1)

            select = Select(escolha)
            select.select_by_visible_text("2ª inst. Judicial")

            self.slp(1)

            body = self.driver.find_element(By.TAG_NAME, "body")
            #ActionChains(self.driver).move_to_element(body).click().perform()

            data = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "data"))
            )
            data.click()
            data.send_keys(data_para_enviar)
            self.slp(1)

    def atualizar_data(self, nova_data):
        data = self.driver.find_element(By.NAME, "data")
        data.clear() 
        data.send_keys(nova_data)
        self.slp(1)

    def buscar_aviso(self):
        try:
            manipulator = DataManipulator(self.json_teste)
            aviso = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "aviso"))
            )
            
            if aviso.is_displayed():
                print("Aviso apareceu! Não há diário para a data especificada. É um recesso ou dia facultativo")
                
                data_fornecida_obj = datetime.strptime(self.dia_util_formatado, "%d-%m-%Y") 
                dia_util_formatado = manipulator.passar_dia_util(data_fornecida_obj)
                
                self.dia_util_formatado = dia_util_formatado.strftime('%d-%m-%Y') 
                print(f"Próximo dia útil: {dia_util_formatado}")

                return True  
            
            print("Aviso não apareceu. Tentando novamente.")
            return False  
            
        except Exception as e:
            print(f"Erro ao buscar aviso")
            return False
        
    def salvar_diario_no_banco(self, nome_arquivo, caminho_arquivo):
        data_str = nome_arquivo[2:-4]
        data_formatada = datetime.strptime(data_str, "%Y%m%d").strftime("%Y-%m-%d")
        dia_dir = os.path.join(self.download_dir, data_formatada)

        if not os.path.exists(dia_dir):
            os.makedirs(dia_dir)

        caminho_arquivo_final = os.path.join(dia_dir, nome_arquivo)
        caminho_arquivo_final = os.path.relpath(caminho_arquivo_final, start=os.getcwd())
        os.rename(caminho_arquivo, caminho_arquivo_final)


        novo_diario = {
            "data_diario": data_formatada,
            "tribunal": "TJMG",
            "cadernos": [{
                "caderno": nome_arquivo,
                "status_leitura": False,
                "caminho_arquivo": caminho_arquivo_final
            }]
        }
        self.banco_falso.inserir(novo_diario)

    def verificar_arquivo_existente(self, nome_arquivo):
        data_str = nome_arquivo[2:-4]
        data_formatada = datetime.strptime(data_str, "%Y%m%d").strftime("%Y-%m-%d")
        dia_dir = os.path.join(self.download_dir, data_formatada)

        if os.path.exists(dia_dir):
            arquivos = os.listdir(dia_dir)
            if nome_arquivo in arquivos:
                print(f"O arquivo {nome_arquivo} já foi baixado para o dia {data_formatada}. Pulando para o próximo dia.")
                return True
        return False

    def executar(self):
        while True:
            manipulator = DataManipulator(self.dia_util_formatado)
            dia_util = manipulator.autenticar_recesso(self.dia_util_formatado)  

            if dia_util:
                print(f"É dia útil! Verificando se há diário.")
                self.atualizar_data(self.dia_util_formatado)

                while True:
                    try: 
                        if self.buscar_aviso():
                            print("Indo para o diário mais recente")
                            dia_util = manipulator.autenticar_recesso(self.dia_util_formatado)
                            self.atualizar_data(dia_util)

                    finally:
                        nome_arquivo = self.gerar_nome_arquivo(self.dia_util_formatado)
                        
                        if self.verificar_arquivo_existente(nome_arquivo):
                            self.dia_util_formatado = manipulator.passar_dia_util_str(self.dia_util_formatado)
                            self.atualizar_data(self.dia_util_formatado)
                            continue

                        download_completo = self.monitorar_download(nome_arquivo)

                        if download_completo:
                            print(f"Download concluído para {self.dia_util_formatado}!")

                            caminho_arquivo = os.path.join(self.download_dir, nome_arquivo)
                            caminho_relativo = os.path.relpath(caminho_arquivo, start=os.getcwd())
                            self.salvar_diario_no_banco(nome_arquivo, caminho_relativo)

                            print(f"Diário salvo no banco com a data {self.dia_util_formatado} e caminho {caminho_arquivo}")
                            self.dia_util_formatado = manipulator.passar_dia_util_str(self.dia_util_formatado)
                            self.atualizar_data(self.dia_util_formatado)
                            self.banco_falso.listar_diarios()
                            break
                        else:
                            print(f"Falha ao baixar o arquivo para {self.dia_util_formatado}. Tentando novamente...")
                            self.captchaSolver()
                            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.F5)
                            self.slp(1)

            else:
                print(f"Próximo dia útil: {self.dia_util_formatado}")
                self.atualizar_data(self.dia_util_formatado)



'''dataDeHoje = datetime.now()
json_teste = dataDeHoje.strftime("%d-%m-%Y")

if __name__ == "__main__":
    diario = DownloadRetroativo(json_teste)  
    diario.executar()'''

    
