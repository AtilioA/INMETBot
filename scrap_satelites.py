# import sys
# import logging
# import re
import requests
from bs4 import BeautifulSoup

from multiprocessing import Pool

# import imageio
# import glob
# import shutil
# import itertools
import os


INMET_SATELITE_BRASIL__VPR_URL = "http://www.inmet.gov.br/projetos/cga/capre/sepra/GEO/GOES12/REGIOES/BRASIL/"
TARGET_PAGE_VPR = "http://www.inmet.gov.br/satelites/?area=0&produto=GO_br_VPR&ct=1"
def vpr_last_image():
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(TARGET_PAGE_VPR, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        print('Successful GET request!')
        # Retrieve the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Skip first option element (not a photo)
        # Get option's value if it is a filename (not Mapa or numbers)
        option = html.find_all("option")[1]["value"]
        imageURL = f"{INMET_SATELITE_BRASIL__VPR_URL}{option}"
        return imageURL
    else:
        print("Failed GET request.")
        return None


def images_last_day():
    fp_in = "satelite_vpr_imgs/*.jpg"
    fp_out = "VPR_pillow2.gif"

    # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif
    img, *imgs = [Image.open(f) for f in sorted(glob.glob(fp_in))]
    img.save(fp=fp_out, format='GIF', append_images=imgs,
            save_all=True, duration=200, loop=0)

    frames = images2gif.readGif("VPR_pillow2.gif", False)
    for frame in frames:
        frame.thumbnail((100,100), Image.ANTIALIAS)

    images2gif.writeGif('rose99.gif', frames)


def scrap_page(targetPage):
    headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(targetPage, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        print('Successful GET request!')
        # Retrieve the HTML content
        content = req.content
        html = BeautifulSoup(content, 'html.parser')

        # Skip first option element (not a photo)
        # Get option's value if it is a filename (not Mapa or numbers)
        options = [option["value"] for option in html.find_all("option")[1:] if "Mapa" not in option.text and re.match(r"\s*\d+\s*", option["value"]) is None]
        # print(options)
        print(len(options))
        imagesURLS = [f"{inmetSateliteBrasilVPR_URL}{option}" for option in options]
        print(imagesURLS)
        print(len(imagesURLS))

        readImages = []
        for i, img in enumerate(reversed(imagesURLS[:5])):
            # response = requests.get(img)
            # img = Image.open(BytesIO(response.content))
            # img.save(f'satelite_vpr_imgs/{i}.jpg', 'JPEG', dpi=[300, 300], quality=40)
            # open(f'satelite_vpr_imgs/{i}.jpg', 'wb').write(requests.get(img, allow_redirects=True).content)
            print(f"Processing {img}...")
            readImages.append(imageio.imread(img))
        # print(len(readImages))

        imageio.mimsave('VPR.gif', readImages)
    else:
        print("Failed GET request.")


if __name__ == "__main__":
    targetPage = "http://www.inmet.gov.br/satelites/?area=0&produto=GO_br_VPR&ct=1"
    # images_last_day()
    # optimize("VPR.gif")
    # scrap_page(targetPage)
    print(vpr_last_image())
