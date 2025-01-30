from selenium import webdriver;
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter

import easyocr as eocr
import locale
import numpy as np
import time
import sys
import os
import re

chrome_options = Options()
download_dir = os.path.join(os.getcwd(), "diarios")

if not os.path.exists(download_dir):
    os.makedirs(download_dir)

chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,  
    "download.prompt_for_download": False,        
    "directory_upgrade": True,                    
    "safebrowsing.enabled": "false"               
})

PATH = "chromedriver.exe"
service = Service(PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
data_hoje = datetime.now().strftime("%d de %B de %Y")
data_hoje_dt = datetime.strptime(data_hoje, "%d de %B de %Y") 
data_formatada = data_hoje_dt.strftime("%d de %B de %Y")
data_formatada = data_formatada.replace(data_formatada.split()[2], data_formatada.split()[2].capitalize())

def slp(seconds):
    time.sleep(seconds)
###INPUT TESTE

json_teste = "25-01-2021"

####INPUT TESTE

driver.get("https://www.tjmg.jus.br/portal-tjmg/")
driver.maximize_window()
slp(3)

def preprocess_image(image_path):
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

def monitorar_download(diretorio_download, nome_arquivo_base):
    tentativas = 0
    while tentativas < 1:
        arquivos = os.listdir(diretorio_download)
        for arquivo in arquivos:
            print(f"Verificando arquivo: {arquivo}")
            if arquivo.startswith(nome_arquivo_base) and arquivo.endswith('.crdownload'):
                print(f"Download em andamento: {arquivo}")
                while arquivo.endswith('.crdownload'):
                    print(f"Download ainda em andamento: {arquivo}")
                    slp(1)
                    arquivos = os.listdir(diretorio_download) 
                    for arquivo_atualizado in arquivos:
                        if arquivo_atualizado.startswith(nome_arquivo_base) and arquivo_atualizado.endswith('.PDF'):
                            arquivo = arquivo_atualizado 
                print(f"Download concluído: {arquivo}")
                return True
            elif arquivo.startswith(nome_arquivo_base) and not arquivo.endswith('.crdownload'):
                print(f"Download concluído: {arquivo}")
                return True
        slp(1)
        tentativas += 1
    return False

def gerar_nome_arquivo():
    data_obj = datetime.strptime(json_teste, "%d-%m-%Y")
    return f"SI{data_obj.strftime('%Y%m%d')}.PDF"


def captchaSolver():
    try:
        captcha_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "captcha_image"))
        )
        
        with open('captcha.png', 'wb') as file:
            file.write(captcha_element.screenshot_as_png)
        print("Captcha capturado com sucesso!")
    except Exception as e:
        print(f"Erro ao capturar CAPTCHA: `{e}")

    slp(2)

    image_path = 'captcha.png'
    preprocessed_image = preprocess_image(image_path)
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

    captcha_box = driver.find_element(By.ID, "captcha_text")
    captcha_box.click()
    captcha_box.send_keys(text) 
    captcha_box.send_keys(Keys.RETURN)
    print("Captcha enviado!")


    slp(2)

    nomeArquivo = gerar_nome_arquivo() 
    sucesso = monitorar_download(download_dir, nomeArquivo)

    if sucesso is True:
        print("Download com sucesso")
        return True
    else:
        print("Falha no download")
        return False




#MAIN - DOWNLOAD DO DIÁRIO
try:
    caminhoDiarios = driver.find_element(By.XPATH, '//*[@id="submenu"]/div/div/div[1]/div/div/div/a')
    driver.execute_script("arguments[0].click();", caminhoDiarios)

    slp(1)
    try:
        cookies = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "termo-uso-btn"))
        )
        cookies.click()
    finally:
        caminhoDJe = driver.find_element(By.XPATH, '//*//div[@class=\'introduction\'][contains(text(),\'Diário do Judiciário eletrônico do Tribunal de Justiça de MG\')]')
        caminhoDJe.click()
        slp(1)
        
        edicoesAnteriores = driver.find_element(By.LINK_TEXT, "Edições Anteriores")
        edicoesAnteriores.click()

        escolha = driver.find_element(By.ID, "tipoDiario")
        escolha.click()

        slp(1)

        select = Select(escolha)
        diario = select.select_by_visible_text("2ª inst. Judicial")

        body = driver.find_element(By.TAG_NAME, "body")
        ActionChains(driver).move_to_element(body).click().perform() 

        data = driver.find_element(By.NAME, "data")
        data.click()   
        data.send_keys(json_teste)
        slp(1)
        
        while not captchaSolver():
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.F5)
            print("Tentando CAPTCHA novamente")
            slp(1)  
                         
finally:
    driver.quit()


    
