import re
import json
import requests


def get_cep_city(CEPString):
    """ Lookup CEP's city. """

    lookup = cep_lookup(CEPString)
    if lookup:
        return lookup["localidade"]
    else:
        return None


def cep_lookup(CEPString):
    """ CEP lookup with viacep's API. """

    if matchCepRegex(CEPString):
        return json.loads(requests.get(viacep_request(CEPString)).content)
    else:
        return None


def viacep_request(CEPString):
    """ Make a request to the viacep's API with given CEP. """

    return f'http://www.viacep.com.br/ws/{cep}/json'


def cepReplace(CEPString):
    """ Remove - and space from string. """

    return str.replace("-", "").replace(" ", "")


def matchCepRegex(CEPString):
    """ Try to match regex pattern to string. """

    return re.match('[0-9]{8}', cepReplace(CEPString))
