import logging
import os
import arrow
import re
from pymongo import MongoClient

modelsLogger = logging.getLogger(__name__)
modelsLogger.setLevel(logging.DEBUG)

MONGO_URI = os.environ.get("INMETBOT_MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.INMETBot
alertsCollection = db.Alerts
subscribedChatsCollection = db.SubscribedChats
modelsLogger.debug("Connected to the INMETBot database.")


def get_CEPs(chatID):
    """ Get chat's subscribed CEPs. """

    queryChat = subscribedChatsCollection.find_one({"chatID": chatID})
    if queryChat:
        return queryChat["CEPs"]
    else:
        return None


def is_subscribed(chatID):
    """ Check if chat is subscribed to alerts. """

    queryChat = subscribedChatsCollection.find_one({"chatID": chatID})
    if queryChat:
        return True
    else:
        return False


def unsubscribe_chat(chatID, cep=None):
    """ Unsubscribe chat and/or CEP from alerts. """

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
    """ Subscribe chat and/or CEP from alerts. """

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


def create_subscribed_chats_document(chatID, cep=None):
    """ Serialize chat subscription for database insertion. """
    # STUB

    if cep:
        subscribedChatsDocument = {'chatID': chatID, 'CEPs': [cep]}
    else:
        subscribedChatsDocument = {'chatID': chatID, 'CEPs': []}
    return subscribedChatsDocument


def create_chat_obj(update):
    if update.message.chat.type == "private":
        return PrivateChat(update.effective_chat.id)
    else:
        return GroupChat(update.effective_chat.id)


class Chat():
    def __init__(self, chatID=None):
        self.id = chatID


class PrivateChat():
    def __init__(self, chatID=None):
        self.id = chatID


class GroupChat():
    def __init__(self, chatID=None):
        self.id = chatID


class Alert():
    def __init__(self, alertXML=None, alertDict=None):
        """ Carry information about an alert (reads from XML file or serialize json). """

        if alertXML:
            self.get_id_from_XML(alertXML)
            self.get_event_from_XML(alertXML)
            self.get_severity_from_XML(alertXML)
            self.get_startDate_from_XML(alertXML)
            self.get_endDate_from_XML(alertXML)
            self.get_description_from_XML(alertXML)
            self.get_area_from_XML(alertXML)
            self.get_cities_from_XML(alertXML)
        elif alertDict:
            self.id = alertDict["alertID"]
            self.event = alertDict["event"]
            self.severity = alertDict["severity"]
            self.startDate = arrow.get(alertDict["startDate"])
            self.endDate = arrow.get(alertDict["endDate"])
            self.description = alertDict["description"]
            self.area = alertDict["area"]
            self.cities = alertDict["cities"]
        else:
            self.id = None
            self.event = None
            self.severity = None
            self.startDate = None
            self.endDate = None
            self.description = None
            self.area = None
            self.cities = None
        # self.graphURL = "http://www.inmet.gov.br/portal/alert-as/"

    def __repr__(self):
        """ String representation of alert. """

        return f"Alert ID: {self.id}, Alert event: {self.event}"

    def insert_alert(self):
        """ Insert alert in the database if isn't in the database. """

        queryAlert = alertsCollection.find_one({"alertID": self.id})
        if not queryAlert:
            alertDocument = self.serialize()
            alertDocument["notifiedChats"] = []
            alertsCollection.insert_one(alertDocument)
            modelsLogger.info(f"Inserted new alert: {self}")
        modelsLogger.info("Alert already exists; not inserted.")

    def serialize(self):
        """ Serialize alert for database insertion. """

        alertDocument = {
            "alertID": self.id,
            "event": self.event,
            "severity": self.severity,
            "startDate": self.startDate.for_json(),
            "endDate": self.endDate.for_json(),
            "description": self.description,
            "area": self.area,
            "cities": self.cities,
        }
        return alertDocument

    def get_id_from_XML(self, alertXML):
        """ Extract id string from XML. """

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
    # alertXML = parse_alerts.get_alerts_xml(ignoreModerate=False)[0]
    # alertParsedXML = parse_alerts.parse_alert_xml(alertXML)
    # alertObj = Alert(alertParsedXML)
    # insert_alert(alertObj)
    pass
