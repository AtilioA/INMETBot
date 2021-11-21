import logging
import os
import arrow
import re
import pymongo
from abc import ABC, abstractmethod
from utils import viacep

modelsLogger = logging.getLogger(__name__)
modelsLogger.setLevel(logging.DEBUG)

MONGO_URI = os.getenv("INMETBOT_MONGO_URI")


class BotDatabase:
    """
    The BotDatabase object facilitates connection to the database.

    Attributes
    ----------
    client : MongoClient
        A MongoClient instance.
    db : Database
        the INMETBot database.
    alertsCollection : Collection
        the Alerts collection.
    subscribedChatsCollection : Collection
        the SubscribedChats collection.
    """

    def __init__(self):
        try:
            if not MONGO_URI:
                raise pymongo.errors.ConfigurationError(
                    f"Connection string is {MONGO_URI}"
                )
            # throw ServerSelectionTimeoutError if serverTimeout is exceeded
            serverTimeout = 20000
            self.client = pymongo.MongoClient(
                MONGO_URI, serverSelectionTimeoutMS=serverTimeout
            )
            self.client.server_info()
            modelsLogger.info("Connected to the INMETBot database!")

            self.db = self.client.INMETBot
            self.alertsCollection = self.db.Alerts
            self.subscribedChatsCollection = self.db.SubscribedChats
        except pymongo.errors.ServerSelectionTimeoutError as mongoClientErr:
            modelsLogger.error(
                f"Failed to connect to the INMETBot database: {mongoClientErr}"
            )
            exit(-1)
        except pymongo.errors.ConfigurationError as mongoClientErr:
            modelsLogger.error(
                f"Failed to connect to the INMETBot database: {mongoClientErr}"
            )
            exit(-1)


INMETBotDB = BotDatabase()


class Chat(ABC):
    """
    The Chat class is an abstract class and serves as base class for GroupChat and PrivateChat.
    Parameters
    ----------
    update : Update
        A message's Update object.
    Attributes
    ----------
    id : str
        The id of the chat.
    type : str
        The type of the chat ("private" or "group").
    title : str
        The title of the chat (group's title or user's username).
    CEPs : list : str
        List of subscribed CEPs.
    subscribed : bool
        Whether the chat is subscribed to alerts or not.
    activated : bool
        Whether the chat wants to be notified or not.
    """

    @abstractmethod
    def __init__(self, update):
        self.id = update.message.chat.id
        self.type = "chat"
        self.title = "Abstract chat"
        self.setChatAttrs()
        # self.CEPs = self.get_chat_CEPs()
        # self.subscribed = self.is_subscribed()

    def setChatAttrs(self):
        """Set chat's CEPs list and subscribed status."""

        queryChat = INMETBotDB.subscribedChatsCollection.find_one({"chatID": self.id})
        if queryChat:
            self.subscribed = True
            self.CEPs = queryChat["CEPs"]
            self.activated = queryChat.get("activated", True)
        else:
            self.subscribed = False
            self.CEPs = []
            self.activated = True

    def get_chat_CEPs(self):
        """Get chat's subscribed CEPs."""

        queryChat = INMETBotDB.subscribedChatsCollection.find_one({"chatID": self.id})
        if queryChat:
            return queryChat["CEPs"]
        else:
            return None

    def is_subscribed(chatID):
        """Check if chat is subscribed to alerts."""

        queryChat = INMETBotDB.subscribedChatsCollection.find_one({"chatID": chatID})
        if queryChat:
            return True
        else:
            return False

    def subscribe_chat(self, cep=None):
        """Subscribe chat and/or CEP to alerts.
            Returns
            --------
                String to be used by a chat object depicting what happened.
        """

        if self.subscribed:
            if cep:
                if cep in self.CEPs:  # Chat is already subscribed, no NEW CEP
                    modelsLogger.info("CEP will not be subscribed; already subscribed.")
                    return "CHAT_EXISTS_CEP_EXISTS"
                else:  # Chat is already subscribed, new CEP
                    INMETBotDB.subscribedChatsCollection.update_one(
                        {"chatID": self.id}, {"$push": {"CEPs": cep}}
                    )
                    modelsLogger.info(f"CEP {cep} has been subscribed.")
                    return "CHAT_EXISTS_CEP_SUBSCRIBED"
            else:  # Chat is already subscribed, no CEP
                return "CHAT_EXISTS_NO_CEP"
                modelsLogger.info(f"Chat {self.id} is already subscribed.")
        else:  # Chat is not subscribed, CEP is optional
            chatDocument = self.serialize(cep)
            INMETBotDB.subscribedChatsCollection.insert_one(chatDocument)
            if cep:
                modelsLogger.info(f"Chat {self.id} and CEP {cep} have been subscribed.")
                return "CHAT_AND_CEP_SUBSCRIBED"
            else:
                modelsLogger.info(f"Chat {self.id} has been subscribed.")
                return "CHAT_SUBSCRIBED"

    def unsubscribe_chat(self, cep=None):
        """Unsubscribe chat and/or CEP from alerts.
            Returns
            --------
                String to be used by a chat object depicting what happened.
        """

        if self.subscribed:
            if cep:
                if cep in self.CEPs:  # Chat is subscribed, CEP is subscribed
                    INMETBotDB.subscribedChatsCollection.update_one(
                        {"chatID": self.id}, {"$pull": {"CEPs": cep}}
                    )
                    unsubscribeMessage = (
                        f"🔕 Desinscrevi o CEP {cep} (*{viacep.get_cep_city(cep)}*)."
                    )
                    modelsLogger.info(f"CEP {cep} has been unsubscribed.")
                    return "CHAT_EXISTS_CEP_UNSUBSCRIBED"
                else:  # Chat is subscribed, CEP is not subscribed
                    modelsLogger.info(f"CEP {cep} isn't subscribed.")
                    return "CHAT_EXISTS_CEP_NOT_FOUND"
            else:  # Chat is subscribed, no CEP
                INMETBotDB.subscribedChatsCollection.delete_one({"chatID": self.id})
                modelsLogger.info(f"Chat {self.id} has been unsubscribed.")
                return "CHAT_UNSUBSCRIBED"
        else:  # Chat is not subscribed, CEP is optional
            modelsLogger.info(f"Chat {self.id} has not been unsubscribed.")
            return "CHAT_NOT_UNSUBSCRIBED"
        return unsubscribeMessage

    def check_subscription_status(self):
        """Check chat's subscription status.
            Returns
            --------
            status : string
                Subscription status and subscribed CEPs as single formatted string.
        """

        if self.subscribed:
            if self.CEPs:
                cepMessage = "CEPs inscritos:\n"
                for cep in self.CEPs:
                    cepMessage += f"{cep} (*{viacep.get_cep_city(cep)}*)\n"
            else:
                cepMessage = "Não há CEPs inscritos."

            if self.activated:
                status = ("SUBSCRIBED_ACTIVATED", cepMessage)
            else:
                status = ("SUBSCRIBED_DEACTIVATED", cepMessage)
        else:
            # Unsubscribed chats can't haev zip codes anyways
            cepMessage = ""
            status = ("NOT_SUBSCRIBED", cepMessage)

        return status

    def deactivate(self):
        """ Set chat's activated status to False. """

        if self.activated:
            INMETBotDB.subscribedChatsCollection.update_one(
                {"chatID": self.id}, {"$set": {"activated": False}}
            )
            return "⏸️ Desativei os alertas temporariamente.\nAtive-os novamente com /ativar."
        else:
            return "❕ Os alertas já estão desativados.\nAtive-os novamente com */ativar*."

    def activate(self):
        """ Set chat's activated status to True. """

        if not self.activated:
            INMETBotDB.subscribedChatsCollection.update_one(
                {"chatID": self.id}, {"$set": {"activated": True}}
            )
            return "▶️ Ativei os alertas.\nDesative-os temporariamente com /desativar."
        else:
            return "❕ Os alertas já estão ativados.\nDesative-os temporariamente com */desativar*."

    def toggle_activated(self):
        """ Negate the activated boolean attribute. """

        if self.activated:
            INMETBotDB.subscribedChatsCollection.update_one(
                {"chatID": self.id}, {"$set": {"activated": False}}
            )
            return "⏸️ Desativei os alertas temporariamente.\nAtive-os novamente com /ativar."
        else:
            INMETBotDB.subscribedChatsCollection.update_one(
                {"chatID": self.id}, {"$set": {"activated": True}}
            )
            return "▶️ Ativei os alertas novamente.\nDesative-os com /desativar."

    def serialize(self, cep=None):
        """Serialize chat subscription for database insertion."""

        if cep:
            subscribedChatsDocument = {
                "chatID": self.id,
                "title": self.title,
                "CEPs": [cep],
                "activated": True,
            }
        else:
            subscribedChatsDocument = {
                "chatID": self.id,
                "title": self.title,
                "CEPs": [],
                "activated": True,
            }
        return subscribedChatsDocument


class PrivateChat(Chat):
    """The PrivateChat object can carry information about a private chat.
    Parameters
    ----------
    update : Update
        A message's Update object.
    Attributes
    ----------
    id : str
        The id of the chat.
    type : str
        The type of the chat "private".
    title : str
        The title of the chat (user's username).
    CEPs : list : str
        List of subscribed CEPs.
    subscribed : bool
        Whether the chat is subscribed to alerts or not.
    activated : bool
        Whether the chat wants to be notified or not.
    """

    def __init__(self, update):
        super(PrivateChat, self).__init__(update)
        self.title = update.message.chat.username
        self.type = "private"

    def get_subscribe_message(self, subscribeResult, textArgs, cep=None):
        """Get subscribe message according to subscription result for a private chat."""

        subscribeMessageDict = {
            "CHAT_EXISTS_CEP_EXISTS": f"❕O CEP já está inscrito.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva-se com /desinscrever.\nDesative alertas temporariamente com /desativar.",
            "CHAT_EXISTS_CEP_SUBSCRIBED": f"🔔 Inscrevi o CEP {cep} (*{viacep.get_cep_city(cep)}*).\nDesinscreva CEPs: `/desinscrever {cep}`.\nDesative alertas temporariamente com /desativar.",
            "CHAT_EXISTS_NO_CEP": f"❕Você já está inscrito.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva-se com /desinscrever.\nDesative alertas temporariamente com /desativar.",
            "CHAT_AND_CEP_SUBSCRIBED": f"🔔 Inscrevi você e o CEP {cep} (*{viacep.get_cep_city(cep)}*).\nDesinscreva-se com /desinscrever.\nDesative alertas temporariamente com /desativar.",
            "CHAT_SUBSCRIBED": f"🔔 Inscrevi você.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva-se com /desinscrever.\nDesative alertas temporariamente com /desativar.",
        }

        subscribeMessage = subscribeMessageDict.get(subscribeResult, None)
        return subscribeMessage

    def get_unsubscribe_message(self, unsubscribeResult, cep=None):
        """Get unsubscribe message according to unsubscription result for a private chat."""

        unsubscribeMessageDict = {
            "CHAT_EXISTS_CEP_UNSUBSCRIBED": f"🔕 Desinscrevi o CEP {cep} (*{viacep.get_cep_city(cep)}*).\nDesative alertas temporariamente com /desativar.",
            "CHAT_EXISTS_CEP_NOT_FOUND": f"❌ O CEP {cep} (*{viacep.get_cep_city(cep)}*) não está inscrito.\nAdicione CEPs: `/inscrever {cep}`.\nDesative alertas temporariamente com /desativar.",
            "CHAT_UNSUBSCRIBED": "🔕 Você foi desinscrito dos alertas e quaisquer CEPs inscritos foram removidos.\nInscreva-se novamente com /inscrever.",
            "CHAT_NOT_UNSUBSCRIBED": "❌ Você não está inscrito nos alertas.\nInscreva-se com /inscrever.",
        }

        unsubscribeMessage = unsubscribeMessageDict.get(unsubscribeResult, None)
        return unsubscribeMessage

    def get_subscription_status_message(self, subscriptionStatus):
        """Get subscription status message according to subscription status for a private chat."""

        subscriptionStatusDict = {
            "SUBSCRIBED_ACTIVATED": "🔔 Você está inscrito nos alertas.\n\n",
            "SUBSCRIBED_DEACTIVATED": "🔇 Você está inscrito nos alertas, mas as notificações estão *desativadas*. Ative-as com /ativar.\n\n",
            "NOT_SUBSCRIBED": "🔕 Você não está inscrito nos alertas. ",
        }

        subscriptionStatusMessage = f"{subscriptionStatusDict.get(subscriptionStatus[0])}{subscriptionStatus[1]}"
        return subscriptionStatusMessage

    def toggle_subscription_callback(self, toggle_subscription_callback_func):
        if self.subscribed:
            return toggle_subscription_callback_func()
        else:
            return "❌ Você não está inscrito nos alertas. Inscreva-se com */inscrever*."


class GroupChat(Chat):
    """The GroupChat object can carry information about a group chat.
    Parameters
    ----------
    update : Update
        A message's Update object.
    Attributes
    ----------
    id : str
        The id of the chat.
    type : str
        The type of the chat "private".
    title : str
        The title of the chat (group's title).
    CEPs : list : str
        List of subscribed CEPs.
    subscribed : bool
        Whether the chat is subscribed to alerts or not.
    activated : bool
        Whether the chat wants to be notified or not.
    """

    def __init__(self, update):
        super(GroupChat, self).__init__(update)
        self.title = update.message.chat.title
        self.type = "group"

    def get_subscribe_message(self, subscribeResult, textArgs, cep=None):
        """Get subscribe message according to subscription result for a group chat."""

        subscribeMessageDict = {
            "CHAT_EXISTS_CEP_EXISTS": f"❕O CEP {cep} (*{viacep.get_cep_city(cep)}*) já está inscrito.\nDesinscreva CEPs: `{textArgs[0]} {cep}`.\nDesinscreva o grupo com /desinscrever.\nDesative alertas temporariamente com /desativar.",
            "CHAT_EXISTS_CEP_SUBSCRIBED": f"🔔 Inscrevi o CEP {cep} (*{viacep.get_cep_city(cep)}*).\nDesinscreva CEPs: `/desinscrever {cep}`.\nDesative alertas temporariamente com /desativar.",
            "CHAT_EXISTS_NO_CEP": f"❕O grupo já está inscrito.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva o grupo com /desinscrever.\nDesative alertas temporariamente com /desativar.",
            "CHAT_AND_CEP_SUBSCRIBED": f"🔔 Inscrevi o grupo e o CEP {cep} (*{viacep.get_cep_city(cep)}*).\nDesinscreva o grupo com /desinscrever.\nDesative alertas temporariamente com /desativar.",
            "CHAT_SUBSCRIBED": f"🔔 Inscrevi o grupo.\nAdicione CEPs: `{textArgs[0]} 29075-910`.\nDesinscreva o grupo com /desinscrever.\nDesative alertas temporariamente com /desativar.",
        }

        subscribeMessage = subscribeMessageDict.get(subscribeResult, None)
        return subscribeMessage

    def get_unsubscribe_message(self, unsubscribeResult, cep=None):
        """Get unsubscribe message according to unsubscription result for a group chat."""

        unsubscribeMessageDict = {
            "CHAT_EXISTS_CEP_UNSUBSCRIBED": f"🔕 Desinscrevi o CEP {cep} (*{viacep.get_cep_city(cep)}*).\nDesative alertas temporariamente com /desativar.",
            "CHAT_EXISTS_CEP_NOT_FOUND": f"❌ O CEP {cep} (*{viacep.get_cep_city(cep)}*) não está inscrito.\nAdicione CEPs: `/inscrever {cep}`",
            "CHAT_UNSUBSCRIBED": "🔕 O grupo foi desinscrito dos alertas e quaisquer CEPs inscritos foram removidos.\nInscreva o grupo novamente com /inscrever.",
            "CHAT_NOT_UNSUBSCRIBED": "❌ O grupo não está inscrito nos alertas.\nInscreva-o com /inscrever.",
        }

        unsubscribeMessage = unsubscribeMessageDict.get(unsubscribeResult, None)
        return unsubscribeMessage

    def get_subscription_status_message(self, subscriptionStatus):
        """Get subscription status message according to subscription status for a group chat."""

        subscriptionStatusDict = {
            "SUBSCRIBED_ACTIVATED": "🔔 O grupo está inscrito nos alertas.\n\n",
            "SUBSCRIBED_DEACTIVATED": "🔇 O grupo está inscrito nos alertas, mas as notificações estão *desativadas*. Ative-as com /ativar.\n\n",
            "NOT_SUBSCRIBED": "🔕 O grupo não está inscrito nos alertas. ",
        }

        subscriptionStatusMessage = f"{subscriptionStatusDict.get(subscriptionStatus[0])}{subscriptionStatus[1]}"
        return subscriptionStatusMessage

    def toggle_subscription_callback(self, callback_func):
        if self.subscribed:
            return callback_func()
        else:
            return "❌ O grupo não está inscrito nos alertas. Inscreva-o com /inscrever."


class Alert:
    """The Alert object can carry information about an alert (reads from XML file or json).

    Parameters
    ----------
    alertXML : BeautifulSoup
        A BS4-parsed XML file.
    alertDict : dict
        A dictionary containing the Alert's information.

    Attributes
    ----------
    id : str
        The Alert ID.
    event : str
        The Alert event/header.
    severity : str
        The Alert's severity ("Moderate", "Severe", "Extreme")
    startDate : Arrow
        The date on which the Alert begins.
    endDate : Arrow
        The date on which the Alert expires.
    description : str
        A description of the Alert.
    area : list : str
        List of regions warned by the Alert.
    cities : list : str
        List of cities warned by the Alert.
    """

    def __init__(self, alertXML=None, alertDict=None):
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

    def __repr__(self):
        """String representation of alert."""

        return f"Alert ID: {self.id}, Alert event: {self.event}"

    def insert_alert(self):
        """Insert alert in the database if isn't in the database."""

        # queryAlert = INMETBotDB.alertsCollection.find_one({"alertID": self.id})
        # if not queryAlert:
        alertDocument = self.serialize()
        alertDocument["notifiedChats"] = []
        INMETBotDB.alertsCollection.insert_one(alertDocument)
        modelsLogger.info(f"Inserted new alert: {self}")
        # modelsLogger.info("Alert already exists; not inserted.")

    def determine_severity_emoji(self):
        """Determine emoji for alert message and return it."""

        if isinstance(self.severity, str):
            emojiDict = {
                "Moderate": "⚠️",  # Yellow alert
                "Severe": "🔶",  # Orange alert
                "Extreme": "🚨",  # Red alert
            }
            return emojiDict.get(self.severity.title(), None)
        else:
            logging.error(f"severity is not string: {self.severity}")
            return None

    def get_alert_message(self, location=None, brazil=False):
        """Create alert message string from alert object and return it."""

        severityEmoji = self.determine_severity_emoji()
        if brazil:
            area = ",".join(self.area)
            area = f"\n*Áreas afetadas*: {area}."
        else:  # Omit "áreas afetadas" for region-specific alerts
            area = ""
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
        {area}
        *Vigor*: De {formattedStartDate} a {formattedEndDate}.
        {self.description}
"""
        return messageString

    def serialize(self):
        """Serialize Alert object for database insertion."""

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
        """Extract id string from XML."""

        alertID = alertXML.identifier.text.replace("urn:oid:", "")
        self.id = alertID

    def get_event_from_XML(self, alertXML):
        """Extract event string from XML."""

        eventPattern = r"(.*?)(?= Severidade)"
        rawEvent = alertXML.info.headline.text
        eventMatch = re.search(eventPattern, rawEvent)
        if eventMatch:
            self.event = eventMatch.group(1)

    def get_severity_from_XML(self, alertXML):
        """Extract severity string from XML."""

        rawSeverity = alertXML.info.headline.text
        severityPattern = r"(?<=Severidade Grau: )(.*)"
        severityMatch = re.search(severityPattern, rawSeverity)
        if severityMatch:
            self.severity = severityMatch.group(1)

    def get_description_from_XML(self, alertXML):
        """Extract description string from XML."""

        rawDescription = alertXML.info.description.text
        descriptionPattern = r"INMET publica aviso iniciando em: .*?\. (.*)"
        descriptionMatch = re.search(descriptionPattern, rawDescription)
        if descriptionMatch:
            self.description = descriptionMatch.group(1)

    def get_area_from_XML(self, alertXML):
        """Extract area string from XML, process it and put it in a list."""

        rawArea = alertXML.info.area.areaDesc.text
        areaPattern = r"(?<=Aviso para as áreas: )(.*)"
        areaMatch = re.search(areaPattern, rawArea)
        if areaMatch:
            self.area = [region for region in areaMatch.group(1).split(",")]

    def get_cities_from_XML(self, alertXML):
        """Extract cities string from XML, process it and put it in a list."""

        parameters = alertXML.info.find_all("parameter")
        citiesParameter = None
        for parameter in parameters:
            if "Municipio" in parameter.valueName.text:
                citiesParameter = parameter
        rawCities = citiesParameter.value.text.split(",")
        cities = [re.sub(r"\s\-.*?\)", "", city).strip() for city in rawCities]
        self.cities = cities

    def get_startDate_from_XML(self, alertXML):
        """Extract startDate string from XML (convert to arrow Object)."""

        startDate = arrow.get(str(alertXML.info.onset.text))
        self.startDate = startDate

    def get_endDate_from_XML(self, alertXML):
        """Extract endDate string from XML (convert to arrow Object)."""

        endDate = arrow.get(str(alertXML.info.expires.text))
        self.endDate = endDate


def create_chat_obj(update):
    """Create Private or Group chat object according to chat type."""

    if update.message.chat.type == "private":
        return PrivateChat(update)
    else:
        return GroupChat(update)


if __name__ == "__main__":
    pass
