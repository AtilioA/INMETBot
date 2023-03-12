import logging
from abc import ABC, abstractmethod
from utils import viacep
from db import INMETBotDB

modelsLogger = logging.getLogger(__name__)
modelsLogger.setLevel(logging.DEBUG)


class Chat(ABC):
    """
    The Chat class serves as an Abstract Base Class for GroupChat and PrivateChat.
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

    @classmethod
    def create_chat_obj(cls, update):
        """Create Private or Group chat object according to chat type."""
        if update.message.chat.type == "private":
            return PrivateChat(update)
        else:
            return GroupChat(update)

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
                # Chat and cep are already subscribed; don't subscribe
                if cep in self.CEPs:
                    modelsLogger.info(
                        f"CEP {cep} will not be subscribed; CEP is already subscribed."
                    )
                    return "CHAT_EXISTS_CEP_EXISTS"

                # Check if the city for this CEP is already subscribed (the alerts' granularity is only to the city level)
                # REVIEW: Maybe save cities instead to simplify comparison?
                # self.CEPs shouldn't be too long (1-10 entries), so this cost is negligible
                cityCep = viacep.get_cep_city(cep)
                citiesCEPs = [viacep.get_cep_city(cep) for cep in self.CEPs]

                # City 'is' already subscribed; don't subscribe this CEP
                if cityCep in citiesCEPs:
                    modelsLogger.info(
                        f"CEP {cep} will not be subscribed; city {cityCep} is already subscribed."
                    )
                    return "CHAT_EXISTS_CITY_EXISTS"
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
        """Set chat's activated status to False."""

        if self.activated:
            INMETBotDB.subscribedChatsCollection.update_one(
                {"chatID": self.id}, {"$set": {"activated": False}}
            )
            return "⏸️ Desativei os alertas temporariamente.\nAtive-os novamente com /ativar."
        else:
            return (
                "❕ Os alertas já estão desativados.\nAtive-os novamente com */ativar*."
            )

    def activate(self):
        """Set chat's activated status to True."""

        if not self.activated:
            INMETBotDB.subscribedChatsCollection.update_one(
                {"chatID": self.id}, {"$set": {"activated": True}}
            )
            return "▶️ Ativei os alertas.\nDesative-os temporariamente com /desativar."
        else:
            return "❕ Os alertas já estão ativados.\nDesative-os temporariamente com */desativar*."

    def toggle_activated(self):
        """Negate the activated boolean attribute."""

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
            "CHAT_EXISTS_CEP_EXISTS": f"❕Este CEP já está inscrito.\nDesinscreva-se com /desinscrever.\nDesative alertas temporariamente com /desativar.",
            "CHAT_EXISTS_CITY_EXISTS": f"❕A cidade deste CEP já está inscrita. O nível de granularidade dos alertas é até cidades apenas.\nDesinscreva-se com /desinscrever.\nDesative alertas temporariamente com /desativar.",
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
