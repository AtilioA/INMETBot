import logging
import os
import arrow
import re
import pymongo
from utils.bot_utils import determine_severity_emoji

modelsLogger = logging.getLogger(__name__)
modelsLogger.setLevel(logging.DEBUG)

MONGO_URI = os.environ.get("INMETBOT_MONGO_URI")


class BotDatabase():
    def __init__(self):
        try:
            maxSevSelDelay = 10000

            self.client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=maxSevSelDelay)
            self.client.server_info()
            self.db = self.client.INMETBot
            self.alertsCollection = self.db.Alerts
            self.subscribedChatsCollection = self.db.SubscribedChats

            modelsLogger.info("Connected to the INMETBot database!")
        except pymongo.errors.ServerSelectionTimeoutError as mongoClientErr:
            modelsLogger.error(f"Failed to connect to the INMETBot database: {mongoClientErr}")


INMETBotDB = BotDatabase()


class Chat():
    def __init__(self, update):
        self.id = update.effective_chat.id
        self.type = "chat"
        self.title = "Abstract chat"
        self.set_CEPs_and_subscribed_status()
        # self.CEPs = self.get_chat_CEPs()
        # self.subscribed = self.is_subscribed()

    def set_CEPs_and_subscribed_status(self):
        """ Set chat's object CEPs list and subscribed status. """

        queryChat = INMETBotDB.subscribedChatsCollection.find_one({"chatID": self.id})
        if queryChat:
            self.subscribed = True
            self.CEPs = queryChat["CEPs"]
        else:
            self.subscribed = False
            self.CEPs = []

    def get_chat_CEPs(self):
        """ Get chat's subscribed CEPs. """

        queryChat = INMETBotDB.subscribedChatsCollection.find_one({"chatID": self.id})
        if queryChat:
            return queryChat["CEPs"]
        else:
            return None

    def is_subscribed(chatID):
        """ Check if chat is subscribed to alerts. """

        queryChat = INMETBotDB.subscribedChatsCollection.find_one({"chatID": chatID})
        if queryChat:
            return True
        else:
            return False

    def subscribe_chat(self, cep=None):
        """ Subscribe chat and/or CEP from alerts.

            Return:
                String depicting what happened.
        """

        if self.subscribed:
            if cep:
                if cep in self.CEPs:  # Chat is already subscribed, no NEW CEP
                    modelsLogger.info("CEP will not be subscribed; already subscribed.")
                    return "CHAT_EXISTS_CEP_EXISTS"
                else:  # Chat is already subscribed, new CEP
                    INMETBotDB.subscribedChatsCollection.update_one({"chatID": self.id}, {"$push": {"CEPs": cep}})
                    modelsLogger.info(f"CEP {cep} has been subscribed.")
                    return "CHAT_EXISTS_CEP_SUBSCRIBED"
            else:  # Chat is already subscribed, no CEP
                return "CHAT_EXISTS_NO_CEP"
                modelsLogger.info(f"Chat {self.id} is already subscribed.")
        else:  # Chat is not subscribed, CEP is optional
            chatDocument = self.serialize(cep)
            INMETBotDB.subscribedChatsCollection.insert_one(chatDocument)
            if cep:
                modelsLogger.info(f"Chat {self.id} and CEP {cep} were subscribed.")
                return "CHAT_AND_CEP_SUBSCRIBED"
            else:
                modelsLogger.info(f"Chat {self.id} has been subscribed.")
                return "CHAT_SUBSCRIBED"

    def unsubscribe_chat(self, cep=None):
        """ Unsubscribe chat and/or CEP from alerts.

            Return:
                True if chat or CEP has been unsubscribed, False otherwise.
        """

        if self.subscribed:
            if cep:
                if cep in self.CEPs:  # Chat is subscribed, CEP is subscribed
                    INMETBotDB.subscribedChatsCollection.update_one({"chatID": self.id}, {"$pull": {"CEPs": cep}})
                    unsubscribeMessage = f"🔕 Desinscrevi o CEP {cep}."
                    modelsLogger.info(f"CEP {cep} has been unsubscribed.")
                    return "CHAT_EXISTS_CEP_UNSUBSCRIBED"
                else:  # Chat is subscribed, CEP is not subscribed
                    modelsLogger.info(f"CEP {cep} isn't subscribed.")
                    return "CHAT_EXISTS_CEP_NOT_FOUND"
            else:  # Chat is subscribed, no CEP
                INMETBotDB.subscribedChatsCollection.delete_one({"chatID": self.id})
                modelsLogger.info(f"Chat {self.id} has been unsubscribed.")
                return "CHAT_UNSUBSCRIBED"
        else:   # Chat is not subscribed, CEP is optional
            modelsLogger.info(f"Chat {self.id} has not been unsubscribed.")
            return "CHAT_NOT_UNSUBSCRIBED"
        return unsubscribeMessage

    def check_subscription_status(self):
        """ Check chat's subscription status.
            Return:
                String with subscription status and subscribed CEPs.
        """

        if self.subscribed:
            if self.CEPs:
                cepMessage = "CEPs inscritos:\n"
                for cep in self.CEPs:
                    cepMessage += f"{cep}\n"
            else:
                cepMessage = "Não há CEPs inscritos."
            status = ("SUBSCRIBED", cepMessage)
        else:
            cepMessage = "Não há CEPs inscritos."
            status = ("NOT_SUBSCRIBED", cepMessage)

        return status

    def serialize(self, cep=None):
        """ Serialize chat subscription for database insertion. """

        if cep:
            subscribedChatsDocument = {'chatID': self.id, "title": self.title, 'CEPs': [cep]}
        else:
            subscribedChatsDocument = {'chatID': self.id, "title": self.title, 'CEPs': []}
        return subscribedChatsDocument


class PrivateChat(Chat):
    def __init__(self, update):
        super(PrivateChat, self).__init__(update)
        self.title = update.message.chat.username
        self.type = "private"

    def get_subscribe_message(self, subscribeResult, textArgs, cep=None):
        subscribeMessageDict = {
            "CHAT_EXISTS_CEP_EXISTS": f"❕Você já está inscrito.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva-se com /desinscrever.",
            "CHAT_EXISTS_CEP_SUBSCRIBED": f"🔔 Inscrevi o CEP {cep}.\nDesinscreva CEPs: `/desinscrever {cep}`.",
            "CHAT_EXISTS_NO_CEP": f"❕Você já está inscrito.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva-se com /desinscrever.",
            "CHAT_AND_CEP_SUBSCRIBED": f"🔔 Inscrevi você e o CEP {cep}.\nDesinscreva-se com /desinscrever.",
            "CHAT_SUBSCRIBED": f"🔔 Inscrevi você.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva-se com /desinscrever."
        }

        subscribeMessage = subscribeMessageDict.get(subscribeResult, None)
        return subscribeMessage

    def get_unsubscribe_message(self, unsubscribeResult, textArgs, cep=None):
        unsubscribeMessageDict = {
            "CHAT_EXISTS_CEP_UNSUBSCRIBED": f"🔕 Desinscrevi o CEP {cep}.",
            "CHAT_EXISTS_CEP_NOT_FOUND": f"❌ O CEP {cep} não está inscrito.\nAdicione CEPs: `/inscrever {cep}`",
            "CHAT_UNSUBSCRIBED": "🔕 Você foi desinscrito dos alertas.\nInscreva-se com /inscrever.",
            "CHAT_NOT_UNSUBSCRIBED": "❌ Você não está inscrito nos alertas.\nInscreva-se com /inscrever."
        }

        unsubscribeMessage = unsubscribeMessageDict.get(unsubscribeResult, None)
        return unsubscribeMessage

    def get_subscription_status_message(self, subscriptionStatus):
        subscriptionStatusDict = {
            "SUBSCRIBED": "Você está inscrito nos alertas.\n\n",
            "UNSUBSCRIBED": "Você não está inscrito nos alertas."
        }

        subscriptionStatusMessage = subscriptionStatusDict.get(subscriptionStatus[0]) + subscriptionStatus[1]
        return subscriptionStatusMessage


class GroupChat(Chat):
    def __init__(self, update):
        super(GroupChat, self).__init__(update)
        self.title = update.message.chat.title
        self.type = "group"

    def get_subscribe_message(self, subscribeResult, textArgs, cep=None):
        subscribeMessageDict = {
            "CHAT_EXISTS_CEP_EXISTS": f"❕O CEP {cep} já está inscrito.\nDesinscreva CEPs: `{textArgs[0]} {cep}`.\nDesinscreva o grupo com /desinscrever.",
            "CHAT_EXISTS_CEP_SUBSCRIBED": f"🔔 Inscrevi o CEP {cep}.\nDesinscreva CEPs: `/desinscrever {cep}`.",
            "CHAT_EXISTS_NO_CEP": f"❕O grupo já está inscrito.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva o grupo com /desinscrever.",
            "CHAT_AND_CEP_SUBSCRIBED": f"🔔 Inscrevi o grupo e o CEP {cep}.\nDesinscreva o grupo com /desinscrever.",
            "CHAT_SUBSCRIBED": f"🔔 Inscrevi o grupo.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva o grupo com /desinscrever."
        }

        subscribeMessage = subscribeMessageDict.get(subscribeResult, None)
        return subscribeMessage

    def get_unsubscribe_message(self, unsubscribeResult, textArgs, cep=None):
        unsubscribeMessageDict = {
            "CHAT_EXISTS_CEP_UNSUBSCRIBED": f"🔕 Desinscrevi o CEP {cep}.",
            "CHAT_EXISTS_CEP_NOT_FOUND": f"❌ O CEP {cep} não está inscrito.\nAdicione CEPs: `/inscrever {cep}`",
            "CHAT_UNSUBSCRIBED": "🔕 O grupo foi desinscrito dos alertas.\nInscreva o grupo com /inscrever.",
            "CHAT_NOT_UNSUBSCRIBED": "❌ O grupo não está inscrito nos alertas.\nInscreva-o com /inscrever.",
        }

        unsubscribeMessage = unsubscribeMessageDict.get(unsubscribeResult, None)
        return unsubscribeMessage

    def get_subscription_status_message(self, subscriptionStatus):
        subscriptionStatusDict = {
            "SUBSCRIBED": "O grupo está inscrito nos alertas.\n\n",
            "UNSUBSCRIBED": "O grupo não está inscrito nos alertas."
        }

        subscriptionStatusMessage = subscriptionStatusDict.get(subscriptionStatus[0]) + subscriptionStatus[1]
        return subscriptionStatusMessage


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

        queryAlert = INMETBotDB.alertsCollection.find_one({"alertID": self.id})
        if not queryAlert:
            alertDocument = self.serialize()
            alertDocument["notifiedChats"] = []
            INMETBotDB.alertsCollection.insert_one(alertDocument)
            modelsLogger.info(f"Inserted new alert: {self}")
        modelsLogger.info("Alert already exists; not inserted.")

    def get_alert_message(self, location=None):
        """ Create alert message string from alert object and return it. """

        severityEmoji = determine_severity_emoji(self.severity)
        area = ','.join(self.area)
        formattedStartDate = self.startDate.strftime("%d/%m/%Y %H:%M")
        formattedEndDate = self.endDate.strftime("%d/%m/%Y %H:%M")

        if isinstance(location, list):
            header = f"{severityEmoji} *{self.event[:-1]} para {', '.join(location)}.*"
        elif location:
            header = f"{severityEmoji} *{self.event[:-1]} para {location}.*"
        else:
            header = f"{severityEmoji} *{self.event}*"

        messageString = f"""
{header}

        *Áreas afetadas*: {area}.
        *Vigor*: De {formattedStartDate} a {formattedEndDate}.
        {self.description}
"""
        return messageString

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


def create_chat_obj(update):
    """ Creates Private or Group chat object according to chat type """

    if update.message.chat.type == "private":
        return PrivateChat(update)
    else:
        return GroupChat(update)


if __name__ == '__main__':
    pass
