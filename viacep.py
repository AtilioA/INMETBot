import re
import json
import requests


def get_cep_city(CEP):
    lookup = cep_lookup(CEP)
    if lookup:
        return lookup["localidade"]
    else:
        return None


def cep_lookup(CEP):
    if matchCepRegex(CEP):
        return json.loads(requests.get(viacep_request(CEP)).content)
    else:
        return None


def viacep_request(cep):
    return f'http://www.viacep.com.br/ws/{cep}/json'


def cepReplace(str):
    return str.replace("-", "").replace(" ", "")


def matchCepRegex(str):
    return re.match('[0-9]{8}', cepReplace(str))
