from selenium import webdriver;
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from DataManipulator import DataManipulator

from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter
 
import requests
import easyocr as eocr
import locale
import numpy as np
import time
import os
import re


class DownloadRetroativo:
    def __init__(self, json_teste):
        self.download_dir = os.path.join(os.getcwd(), "diarios")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        self.chrome_options = Options()
        self.chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
            "safebrowsing.enabled": "false"
        })

        self.PATH = "chromedriver.exe"
        self.service = Service(self.PATH)
        self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)

        self.json_teste = json_teste
        self.data_formatada = self.get_data_formatada()

        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

    def get_data_formatada(self):
        data_hoje = datetime.now().strftime("%d de %B de %Y")
        data_hoje_dt = datetime.strptime(data_hoje, "%d de %B de %Y")
        data_formatada = data_hoje_dt.strftime("%d de %B de %Y")
        return data_formatada.replace(data_formatada.split()[2], data_formatada.split()[2].capitalize())

    def slp(self, seconds):
        time.sleep(seconds)

    #def dados_jsonGET(self):
     #       urlAPI = "URL DA API"
      #      responseGet = requests.get(urlAPI)
#
 #           if responseGet.status_code == 200:
  #              dados = responseGet.json()
#            for item in dados:
  #              dataAPI = item.get('data_diario')
   #             tribunalAPI = item.get('tribunal')
    #        
     #       print(dataAPI, tribunalAPI)
#
 #   def dados_jsonPOST(self):
  #          urlAPI = "URL DA API"
   #         caminho_pdf = "diarios/" + self.gerar_nome_arquivo()
#
 #           if os.path.exists(caminho_pdf):
  #              info = {
   #                 "nome": self.gerar_nome_arquivo(),
    #                "status_leitura": "teste",
     #           }
      #          with open(caminho_pdf, 'rb') as file:
#
 #                   arquivo = {
  #                      'arquivo_pdf': (os.path.basename(caminho_pdf), file, 'application/pdf')  # Passa o arquivo
   #                 }
#
 #                   response_post = requests.post(urlAPI, data=info, files=arquivo)
#
 #                   if response_post.status_code == 201:
  #                      print("Dados enviados com sucesso!")
   #                     resposta_json = response_post.json()
    #                    print(resposta_json)
     #               else:
      #                  print("Erro ao enviar dados para a API:", response_post.status_code)
      
    def preprocess_image(self, image_path):
        img = Image.open(image_path)
        contrast = ImageEnhance.Contrast(img)
        sharpness = ImageEnhance.Sharpness(img)
        img = img.filter(ImageFilter.SMOOTH)
        img = contrast.enhance(6.0)
        img = sharpness.enhance(8.0)
        img_rgb = img.convert('RGB')
        np_img = np.array(img_rgb)

        black_mask = np_img[:, :, 0] <= 50
        np_img[black_mask] = np_img[black_mask] + 60

        red_min = 25
        red_mask = (np_img[:, :, 0] >= red_min) & (np_img[:, :, 1] <= 100) & (np_img[:, :, 2] <= 100)
        np_img[~red_mask] = 255

        img_red = Image.fromarray(np_img)
        preprocessed_image_path = 'preprocessed_captcha.png'
        img_red.save(preprocessed_image_path)
        return img_red

    def monitorar_download(self, nome_arquivo_base):
        tentativas = 0
        while tentativas < 1:
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

    def gerar_nome_arquivo(self):
        data_obj = datetime.strptime(self.json_teste, "%d-%m-%Y")
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

        nome_arquivo = self.gerar_nome_arquivo()
        sucesso = self.monitorar_download(nome_arquivo)

        if sucesso:
            print("Download com sucesso")
            return True
        else:
            print("Falha no download")
            return False

    def acessar_site(self):
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

            body = self.driver.find_element(By.TAG_NAME, "body")
            ActionChains(self.driver).move_to_element(body).click().perform()

            data = self.driver.find_element(By.NAME, "data")
            data.click()
            data.send_keys(self.json_teste)
            self.slp(1)

    def executar(self):
        self.acessar_site()
        if not self.buscar_diario():  
            print("Indo para o diário mais recente")
            manipulator = DataManipulator.passar_dia_util(self.data_formatada)
            manipulator.passar_dia_util(self.data_formatada)
            return self.executar()
        
        while not self.captchaSolver():
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.F5)
            print("Tentando CAPTCHA novamente")
            self.slp(1)

        print("Download completo!")
        self.driver.quit()


if __name__ == "__main__":
    json_teste = "26-01-2025"  # A data de teste
    diario = DownloadRetroativo(json_teste)
    diario.executar()


    
