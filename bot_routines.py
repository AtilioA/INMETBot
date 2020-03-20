import arrow
import logging
from scraping import parse_alerts
import models
from utils import viacep
from bot_config import updater
from bot_functions import MAX_ALERTS_PER_MESSAGE

routinesLogger = logging.getLogger(__name__)
routinesLogger.setLevel(logging.DEBUG)


def delete_past_alerts_routine():
    """Delete past alerts published by INMET from the database."""

    alerts = list(models.INMETBotDB.alertsCollection.find({}))
    timeNow = arrow.utcnow().to("Brazil/East")
    for alert in alerts:
        if timeNow > arrow.get(alert["endDate"]):
            routinesLogger.info(
                f"alert {alert['alertID']} is past and will be deleted.")
            models.INMETBotDB.alertsCollection.delete_one(
                {"alertID": alert["alertID"]})
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
    alerts = parse_alerts.instantiate_alerts_objects(alertsXML, ignoreModerate)
    routinesLogger.info(f"New alerts found: {alerts}")
    for alert in alerts:
        alert.insert_alert()
    routinesLogger.info("Finished parse_alerts_routine routine.")


def notify_chats_routine():
    """
    Check alerts from the database and notify chats.

    For every alert and chat, check if chat has been notified for that alert; if it has not, check if there is any city (obtained by CEPs in the chat's CEP list) that is included in the alert.
    If there is, notify chat and mark chat as notified (so it won't get notified again for the same alert).
    """

    subscribedChats = list(
        models.INMETBotDB.subscribedChatsCollection.find({}))
    alertMessage = ""
    alertCounter = 1

    for chat in subscribedChats:
        if chat["activated"]:
            routinesLogger.debug(f"- Checking chat {chat['chatID']}")
            for cep in chat["CEPs"]:
                try:
                    city = viacep.get_cep_city(cep)
                    routinesLogger.debug(f"Checking {city}...")
                except Exception as error:
                    routinesLogger.warning(f"Viacep error: {error}")
                    continue

                # Get alerts, by city, that weren't notified to this chat
                alerts = list(models.INMETBotDB.alertsCollection.find(
                    {"$and": [
                        {"cities": city}, {"notifiedChats": {
                            "$ne": chat["chatID"]}}
                    ]}
                ))
                if alerts:
                    # Any alert here is to be sent to the chat,
                    # since they affect a zipcode and the chat hasn't been notified yet
                    alertMessage = ""
                    routinesLogger.info(
                        f"-- Existing alert for {city}. --")
                    for alert in alerts:
                        if alertCounter >= MAX_ALERTS_PER_MESSAGE:
                            updater.bot.send_message(
                                chat_id=chat['chatID'], text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)
                            alertMessage = ""
                            alertCounter = 1
                        alertObj = models.Alert(alertDict=alert)
                        alertMessage += alertObj.get_alert_message(city)
                        routinesLogger.info(
                            f"-- Notifying chat {chat['chatID']} about alert {alert['alertID']}... --")

                        models.INMETBotDB.alertsCollection.update_one({"alertID": alert["alertID"]}, {
                            "$addToSet": {"notifiedChats": chat['chatID']}})
                        alertCounter += 1

                    # "Footer" message after all alerts
                    alertMessage += "\nMais informações em http://www.inmet.gov.br/portal/alert-as/"

                    updater.bot.send_message(
                        chat_id=chat['chatID'], text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)
    routinesLogger.info("Finished notify_chats_routine routine.")


if __name__ == "__main__":
    pass
