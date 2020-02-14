# import logging
# import re
import requests
from bs4 import BeautifulSoup

import imageio
# import glob
# import shutil
from datetime import datetime
import re
import os

INMET_DOMAIN = "http://www.inmet.gov.br/"

TARGET_PAGE_VPR = "http://www.inmet.gov.br/satelites/?area=0&produto=GO_br_VPR&ct=1"
INMET_SATELITE_BRASIL_VPR_URL = "http://www.inmet.gov.br/projetos/cga/capre/sepra/GEO/GOES12/REGIOES/BRASIL/"

TARGET_PAGE_ACUMULADA = "http://www.inmet.gov.br/portal/index.php?r=tempo2/mapasPrecipitacao"
TARGET_PAGE_ACUMULADA_PREVISAO_24HRS = "http://www.inmet.gov.br/vime/?H=24&A=BRA"
INMET_ACUMULADA_PREVISAO_24HRS_URL = "http://www.inmet.gov.br/projetos/cga/capre/cosmo7/BRA/prec24h/"

def get_vpr_last_image():
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(TARGET_PAGE_VPR, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        print('Successful GET request to VPR page!')
        # Retrieve the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Skip first option element (not a photo)
        option = html.find_all("option")[1]["value"]
        imageURL = f"{INMET_SATELITE_BRASIL_VPR_URL}{option}"
        return imageURL
    else:
        print("Failed GET request.")
        return None


def get_acumulada_last_image(interval):
    stringInterval = str(interval).zfill(2)
    # If interval is none of the options available
    if stringInterval not in ["01", "03", "05", "10", "15", "30", "90"]:
        return None

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(TARGET_PAGE_ACUMULADA, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        print('Successful GET request to MAPAS DE PRECIPITAÇÃO page!')
        # Retrieve the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Get value of first option element
        selectTag = html.find("select", id=f"data_{stringInterval}d")
        option = selectTag.find_all("option")[0]["value"]

        imageURL = f"{INMET_DOMAIN}{option}"
        return imageURL
    else:
        print("Failed GET request.")
        return None


def get_acumulada_previsao_24hrs():
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(TARGET_PAGE_ACUMULADA_PREVISAO_24HRS, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        print('Successful GET request to MAPAS DE PRECIPITAÇÃO page!')
        # Retrieve the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Get value of first option element
        selectTag = html.find("select")
        option = selectTag.find_all("option")[0]["value"]

        imageURL = f"{INMET_ACUMULADA_PREVISAO_24HRS_URL}{option}"
        print(imageURL)
        return imageURL
    else:
        print("Failed GET request.")
        return None


def get_vpr_gif(nImages):
    if 1 > nImages > 10:
        nImages = 10

    headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(TARGET_PAGE_VPR, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        print('Successful GET request!')
        # Retrieve the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Skip first option element (not a photo)
        # Get option's value if it is a filename (not Mapa or numbers)
        options = [option["value"] for option in html.find_all("option")[1:] if "Mapa" not in option.text and re.match(r"\s*\d+\s*", option["value"]) is None]
        imagesURLS = [f"{INMET_SATELITE_BRASIL_VPR_URL}{option}" for option in options]


        readImages = []
        for i, img in enumerate(reversed(imagesURLS[:5])):
            # img = Image.open(BytesIO(response.content))
            # img.save(f'satelite_vpr_imgs/{i}.jpg', 'JPEG', dpi=[300, 300], quality=40)
            # open(f'satelite_vpr_imgs/{i}.jpg', 'wb').write(requests.get(img, allow_redirects=True).content)
            print(f"Processing {img}...")
            readImages.append(imageio.imread(img))
        # print(len(readImages))

        imageio.mimsave('VPR.gif', readImages, fps=2)
    else:
        print("Failed GET request.")


if __name__ == "__main__":
    # print(get_acumulada_last_image(1))
    get_acumulada_previsao_24hrs()
    pass
