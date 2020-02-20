import logging
import os
import re
import requests
from bs4 import BeautifulSoup
import imageio
import arrow

scrapingLogger = logging.getLogger(__name__)
scrapingLogger.setLevel(logging.DEBUG)

MIN_VPR_IMAGES = 2
DEFAULT_VPR_IMAGES = 9  # 2 hours of images
MAX_VPR_IMAGES = 40

INMET_DOMAIN = "http://www.inmet.gov.br/"

TARGET_PAGE_VPR = "http://www.inmet.gov.br/satelites/?area=0&produto=GO_br_VPR&ct=1"
INMET_SATELITE_BRASIL_VPR_URL = "http://www.inmet.gov.br/projetos/cga/capre/sepra/GEO/GOES12/REGIOES/BRASIL/"

TARGET_PAGE_ACUMULADA = "http://www.inmet.gov.br/portal/index.php?r=tempo2/mapasPrecipitacao"
TARGET_PAGE_ACUMULADA_PREVISAO_24HRS = "http://www.inmet.gov.br/vime/?H=24&A=BRA"
INMET_ACUMULADA_PREVISAO_24HRS_URL = "http://www.inmet.gov.br/projetos/cga/capre/cosmo7/BRA/prec24h/"


def get_vpr_last_image():
    """ Fetch the last VPR satellite image.

    Return:
        Image URL if successful, None otherwise.
    """

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(TARGET_PAGE_VPR, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        scrapingLogger.info("Successful GET request to VPR page!")
        # Retrieve the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Skip first option element (not a photo)
        option = html.find_all("option")[1]["value"]
        imageURL = f"{INMET_SATELITE_BRASIL_VPR_URL}{option}"
        return imageURL
    else:
        scrapingLogger.error("Failed GET request to VPR page.")
        return None


def get_acumulada_last_image(interval):
    """ Fetch the last accumulated precipitation (within given interval) satellite image.

    Args:
        interval: numbers of days to consider in the accumulated precipitation measurement. Is used to fetch image.
    Return:
        Image URL if successful, None otherwise.
    """

    stringInterval = str(interval).zfill(2)
    # If interval is none of the options available
    if stringInterval not in ["01", "03", "05", "10", "15", "30", "90"]:
        return None

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(TARGET_PAGE_ACUMULADA, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        scrapingLogger.info("Successful GET request to MAPAS DE PRECIPITAÇÃO page!")
        # Retrieve the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Get value of first option element
        selectTag = html.find("select", id=f"data_{stringInterval}d")
        option = selectTag.find_all("option")[0]["value"]

        imageURL = f"{INMET_DOMAIN}{option}"
        return imageURL
    else:
        scrapingLogger.error("Failed GET request to MAPAS DE PRECIPITAÇÃO page.")
        return None


def get_acumulada_previsao_24hrs():
    """ Fetch the last accumulated precipitation for the next 24 hours satellite image.

    Return:
        Image URL if successful, `None` otherwise.
    """

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(TARGET_PAGE_ACUMULADA_PREVISAO_24HRS, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        scrapingLogger.info("Successful GET request to MAPAS DE PRECIPITAÇÃO (forecast) page!")
        # Retrieve the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Get value of first option element
        selectTag = html.find("select")
        option = selectTag.find_all("option")[0]["value"]

        imageURL = f"{INMET_ACUMULADA_PREVISAO_24HRS_URL}{option}"
        scrapingLogger.debug(imageURL)
        return imageURL
    else:
        scrapingLogger.error("Failed GET request to MAPAS DE PRECIPITAÇÃO (forecast) page.")
        return None


def get_vpr_gif(nImages=DEFAULT_VPR_IMAGES):
    """ Fetch the last `nImages` VPR sattelite images and create a .mp4 file.

        Return:
            mp4 filename if successful, None otherwise.
    """

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }

    req = requests.get(TARGET_PAGE_VPR, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        scrapingLogger.info('Successful GET request to VPR page!')
        # Retrieve the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Skip first option element (not a photo)
        # Get option's value if it is a filename (not Mapa or numbers)
        options = [option["value"] for option in html.find_all("option")[1:] if "Mapa" not in option.text and re.match(r"\s*\d+\s*", option["value"]) is None]
        imagesURLS = [f"{INMET_SATELITE_BRASIL_VPR_URL}{option}" for option in options]

        readImages = []
        scrapingLogger.debug((f"Reading {imagesURLS[:1]}..."))
        for img in reversed(imagesURLS[:nImages]):
            readImages.append(imageio.imread(img))
        scrapingLogger.debug(f"Read {(len(readImages))} images.")

        timeNow = arrow.utcnow().timestamp
        gifFilename = os.path.join("tmp", f"VPR_{timeNow}.mp4")
        kargs = {'fps': 10, 'macro_block_size': None}
        imageio.mimsave(f'{gifFilename}', readImages, 'MP4', **kargs)

        return gifFilename
    else:
        scrapingLogger.error("Failed GET request to VPR page.")
        return None


if __name__ == "__main__":
    get_vpr_gif(3)
