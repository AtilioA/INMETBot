import arrow
import requests
import logging
import models
from telegram.error import TelegramError
from utils import viacep, parse_alerts, bot_messages
from bot_config import updater

routinesLogger = logging.getLogger(__name__)
routinesLogger.setLevel(logging.DEBUG)


def ping(URL):
    requests.get(URL)
    routinesLogger.info(f"Pinged {URL}.")


def delete_past_alerts_routine():
    """Delete past alerts published by INMET from the database."""

    alerts = list(models.INMETBotDB.alertsCollection.find({}))
    timeNow = arrow.utcnow().to("Brazil/East")
    for alert in alerts:
        if timeNow > arrow.get(alert["endDate"]):
            routinesLogger.info(
                f"alert {alert['alertID']} is past and will be deleted."
            )
            models.INMETBotDB.alertsCollection.delete_one({"alertID": alert["alertID"]})
    routinesLogger.info("Finished delete_past_alerts_routine routine.")


def parse_alerts_routine(ignoreModerate=False):
    """
    Parse alerts published by INMET and insert them into database.

    Parameters
    --------
    ignoreModerate : bool
        If set to True, will ignore alerts of moderate severity. Defaults to False.
    """

    alertsXML = parse_alerts.parse_alerts_xml(ignoreModerate)
    if alertsXML:
        alerts = parse_alerts.instantiate_alerts_objects(alertsXML, ignoreModerate)
        routinesLogger.info(f"New alerts found: {alerts}")
        for alert in alerts:
            alert.insert_alert()
        routinesLogger.info("Finished parse_alerts_routine routine.")


# TODO: Reduce code duplication.
def notify_chats_routine():
    """
    Check alerts from the database and notify chats.

    For every alert and chat, check if chat has been notified for that alert; if it has not, check if there is any city (obtained by CEPs in the chat's CEP list) that is included in the alert.
    If there is, notify chat and mark chat as notified (so it won't get notified again for the same alert).
    """

    subscribedChats = list(models.INMETBotDB.subscribedChatsCollection.find({}))
    alertMessage = ""
    alertCounter = 1

    for chat in subscribedChats:
        cities = []
        if chat["activated"]:
            routinesLogger.debug(f"Checking chat {chat['chatID']}")
            try:
                cities = [viacep.get_cep_city(cep) for cep in chat["CEPs"]]
            except Exception as error:
                routinesLogger.error(
                    f"Unknown error when getting CEPs for chat {chat}: {error}"
                )
                pass
            for cep in chat["CEPs"]:
                try:
                    city = viacep.get_cep_city(cep)
                    routinesLogger.debug(f"- Checking {city}...")
                except Exception as error:
                    routinesLogger.warning(f"Viacep error: {error}")
                    continue

                # Get alerts, by city, that weren't notified to this chat
                alerts = list(
                    models.INMETBotDB.alertsCollection.find(
                        {
                            "$and": [
                                {"cities": city},
                                {"notifiedChats": {"$ne": chat["chatID"]}},
                            ]
                        }
                    )
                )

                if alerts:
                    # Any alerts here are to be sent to the chat,
                    # since they affect a zip code and the chat hasn't been notified yet
                    alertMessage = ""
                    routinesLogger.info(f"-- Existing alert for {city}. --")
                    for alert in alerts:
                        if alertCounter >= bot_messages.MAX_ALERTS_PER_MESSAGE:
                            try:
                                updater.bot.send_message(
                                    chat_id=chat["chatID"],
                                    text=alertMessage,
                                    parse_mode="markdown",
                                    disable_web_page_preview=True,
                                )
                            except Exception as error:
                                routinesLogger.error(
                                    f"ERRO: unable to send message to {chat['chatID']} ({chat['title']}): {error}.\nRemoving chat from DB......"
                                )
                                models.INMETBotDB.subscribedChatsCollection.delete_one(
                                    {"chatID": chat["chatID"]}
                                )

                                alertMessage = ""
                                alertCounter = 1

                        alertObj = models.Alert(alertDict=alert)

                        affectedCities = [
                            city for city in cities if city in alertObj.cities
                        ]

                        alertMessage += alertObj.get_alert_message(affectedCities)
                        routinesLogger.info(
                            f"-- Notifying chat {chat['chatID']} about alert {alert['alertID']}... --"
                        )

                        models.INMETBotDB.alertsCollection.update_one(
                            {"alertID": alert["alertID"]},
                            {"$addToSet": {"notifiedChats": chat["chatID"]}},
                        )
                        alertCounter += 1

                    # "Footer" message after all alerts
                    alertMessage += f"\nMais informações em {bot_messages.ALERTAS_URL}."

                    try:
                        updater.bot.send_message(
                            chat_id=chat["chatID"],
                            text=alertMessage,
                            parse_mode="markdown",
                            disable_web_page_preview=True,
                        )
                    except Exception as error:
                        routinesLogger.error(
                            f"ERRO: unable to send message to {chat['chatID']} ({chat['title']}): {error}.\nRemoving chat from DB......"
                        )
                        models.INMETBotDB.subscribedChatsCollection.delete_one(
                            {"chatID": chat["chatID"]}
                        )
    routinesLogger.info("Finished notify_chats_routine routine.")


if __name__ == "__main__":
    pass
