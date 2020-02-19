import logging
import os
import arrow
import re
from pymongo import MongoClient
import parse_alerts

modelsLogger = logging.getLogger(__name__)
modelsLogger.setLevel(logging.DEBUG)

MONGO_URI = os.environ.get("INMETBOT_MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.INMETBot
alertsCollection = db.Alerts
subscribedChatsCollection = db.SubscribedChats
modelsLogger.debug("Connected to the INMETBot database.")


def get_CEPs(chatID):
    queryChat = subscribedChatsCollection.find_one({"chatID": chatID})
    if queryChat:
        return queryChat["CEPs"]
    else:
        return None


def is_subscribed(chatID):
    queryChat = subscribedChatsCollection.find_one({"chatID": chatID})
    if queryChat:
        return True
    else:
        return False


def unsubscribe_chat(chatID, cep=None):
    if cep:
        queryChat = subscribedChatsCollection.find_one({"chatID": chatID})
        if queryChat:
            if cep in queryChat["CEPs"]:
                subscribedChatsCollection.update_one({"chatID": chatID}, {"$pull": {"CEPs": cep}})
                modelsLogger.info("CEP unsubscribed.")
                return True
            else:
                modelsLogger.info("CEP isn't subscribed.")
                return False
        else:
            modelsLogger.info("Chat isn't subscribed.")
            return False
    else:
        subscribedChatsCollection.delete_one({"chatID": chatID})
        modelsLogger.info("Unsubscribed chat.")
        return True


def subscribe_chat(chatID, cep):
    queryChat = subscribedChatsCollection.find_one({"chatID": chatID})
    if queryChat:
        if cep in queryChat["CEPs"]:
            modelsLogger.info("CEP already subscribed.")
            return False
        else:
            subscribedChatsCollection.update_one({"chatID": chatID}, {"$push": {"CEPs": cep}})
            modelsLogger.info("CEP subscribed!")
            return True
    else:
        modelsLogger.info("Chat not subscribed yet.")
        chatDocument = create_subscribed_chats_document(chatID, cep)
        subscribedChatsCollection.insert_one(chatDocument)
        return True


def insert_alert(alertObj):
    queryAlert = alertsCollection.find_one({"alertID": alertObj.id})
    if not queryAlert:
        alertDocument = create_alert_document(alertObj)
        alertsCollection.insert_one(alertDocument)
        modelsLogger.info("Inserted new alert.")
    modelsLogger.info("Not inserted. Alert already exists.")


def create_alert_document(alertObj):
    alertDocument = {"alertID": alertObj.id, "event": alertObj.event, "severity": alertObj.severity, "startDate": alertObj.startDate.for_json(), "endDate": alertObj.endDate.for_json(), "description": alertObj.description, "area": alertObj.area, "cities": alertObj.cities, "notifiedChats": []}
    return alertDocument


def create_subscribed_chats_document(chatID, cep=None):
    if cep:
        subscribedChatsDocument = {'chatID': chatID, 'CEPs': [cep]}
    else:
        subscribedChatsDocument = {'chatID': chatID, 'CEPs': []}
    return subscribedChatsDocument


class Alert():
    def __init__(self, alertXML=None):
        """ Carry information about an alert (reads from XML file). """

        if alertXML:
            self.get_id_from_XML(alertXML)
            self.get_event_from_XML(alertXML)
            self.get_severity_from_XML(alertXML)
            self.get_startDate_from_XML(alertXML)
            self.get_endDate_from_XML(alertXML)
            self.get_description_from_XML(alertXML)
            self.get_area_from_XML(alertXML)
            self.get_cities_from_XML(alertXML)
        else:
            self.id = ""
            self.event = ""
            self.severity = ""
            self.startDate = ""
            self.endDate = ""
            self.description = ""
            self.area = ""
            self.cities = ""
        self.graphURL = "http://www.inmet.gov.br/portal/alert-as/"

    def get_id_from_XML(self, alertXML):
        alertID = alertXML.identifier.text.replace("urn:oid:", "")
        self.id = alertID

    def get_event_from_XML(self, alertXML):
        """ Extract event string from XML. """

        eventPattern = r"(.*?)(?= Severidade)"
        rawEvent = alertXML.info.headline.text
        eventMatch = re.search(eventPattern, rawEvent)
        if eventMatch:
            self.event = eventMatch.group(1)

    def get_severity_from_XML(self, alertXML):
        """ Extract severity string from XML. """

        rawSeverity = alertXML.info.headline.text
        severityPattern = r"(?<=Severidade Grau: )(.*)"
        severityMatch = re.search(severityPattern, rawSeverity)
        if severityMatch:
            self.severity = severityMatch.group(1)

    def get_description_from_XML(self, alertXML):
        """ Extract description string from XML. """

        rawDescription = alertXML.info.description.text
        descriptionPattern = r"INMET publica aviso iniciando em: .*?\. (.*)"
        descriptionMatch = re.search(descriptionPattern, rawDescription)
        if descriptionMatch:
            self.description = descriptionMatch.group(1)

    def get_area_from_XML(self, alertXML):
        """ Extract area string from XML, process it and put it in a list. """

        rawArea = alertXML.info.area.areaDesc.text
        areaPattern = r"(?<=Aviso para as áreas: )(.*)"
        areaMatch = re.search(areaPattern, rawArea)
        if areaMatch:
            self.area = [region for region in areaMatch.group(1).split(",")]

    def get_cities_from_XML(self, alertXML):
        """ Extract cities string from XML, process it and put it in a list """

        parameters = alertXML.info.find_all("parameter")
        citiesParameter = None
        for parameter in parameters:
            if "Municipio" in parameter.valueName.text:
                citiesParameter = parameter
        rawCities = citiesParameter.value.text.split(',')
        cities = [re.sub(r"\s\-.*?\)", '', city).strip() for city in rawCities]
        self.cities = cities

    def get_startDate_from_XML(self, alertXML):
        """ Extract startDate string from XML (convert to arrow Object). """

        startDate = arrow.get(str(alertXML.info.onset.text))
        self.startDate = startDate

    def get_endDate_from_XML(self, alertXML):
        """ Extract endDate string from XML (convert to arrow Object). """

        endDate = arrow.get(str(alertXML.info.expires.text))
        self.endDate = endDate


if __name__ == '__main__':
    alertXML = parse_alerts.get_alerts_xml(ignoreModerate=False)[0]
    alertParsedXML = parse_alerts.parse_alert_xml(alertXML)
    alertObj = Alert(alertParsedXML)
    insert_alert(alertObj)
