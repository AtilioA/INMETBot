import arrow
import logging
from scraping import parse_alerts
import models
# import pycep_correios as pycep
from utils import viacep
from bot_config import updater

routinesLogger = logging.getLogger(__name__)
routinesLogger.setLevel(logging.DEBUG)


def delete_past_alerts_routine():
    """Delete past alerts published by INMET from the database."""

    alerts = list(models.INMETBotDB.alertsCollection.find({}))
    timeNow = arrow.utcnow().to("Brazil/East")
    for alert in alerts:
        if timeNow > arrow.get(alert["endDate"]):
            routinesLogger.info(f"alert {alert['alertID']} is past and will be deleted.")
            models.INMETBotDB.alertsCollection.delete_one({"alertID": alert["alertID"]})
    routinesLogger.info("Finished delete_past_alerts_routine routine.")


def parse_alerts_routine(ignoreModerate=False):
    """Parse alerts published by INMET and insert them into database.

    Parameters
    --------
    ignoreModerate : bool
        If set to True, will ignore alerts of moderate severity. Defaults to False.
    """

    alertsXML = parse_alerts.parse_alerts_xml(ignoreModerate)
    alerts = parse_alerts.instantiate_alerts_objects(alertsXML, ignoreModerate)
    routinesLogger.info(alerts)
    for alert in alerts:
        alert.insert_alert()
    routinesLogger.info("Finished parse_alerts_routine routine.")


def notify_chats_routine():
    """Check alerts from the database and notify chats.

    For every alert and chat, check if chat has been notified for that alert; if it has not, check if there is any city (obtained by CEPs in the chat's CEP list) that is included in the alert.
    If there is, notify chat and mark chat as notified (so it won't get notified again for the same alert).
    """

    subscribedChats = list(models.INMETBotDB.subscribedChatsCollection.find({}))
    alertMessage = ""

    for chat in subscribedChats:
        routinesLogger.debug(f"- Checking chat {chat['chatID']}")
        for cep in chat["CEPs"]:
            try:
                city = viacep.get_cep_city(cep)
                routinesLogger.debug(f"Checking {city}...")
            except Exception as error:
                routinesLogger.warning(f"Viacep error: {error}")
                continue

            alerts = list(models.INMETBotDB.alertsCollection.find(
                {"$and": [
                    {"cities": city}, {"notifiedChats": {"$ne": chat["chatID"]}}
                ]}
            ))
            if alerts:
                routinesLogger.info(f"-- Warning about {city}. --")
                for alert in alerts:
                    alertObj = models.Alert(alertDict=alert)
                    alertMessage += alertObj.get_alert_message(city)
                    routinesLogger.info(f"-- Notifying chat {chat['chatID']} for alert {alert['alertID']}... --")

                    models.INMETBotDB.alertsCollection.update_one({"alertID": alert["alertID"]}, {"$addToSet": {"notifiedChats": chat['chatID']}})

                alertMessage += "\nMais informações em http://www.inmet.gov.br/portal/alert-as/"
                updater.bot.send_message(chat_id=chat["chatID"], text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)

    routinesLogger.info("Finished notify_chats_routine routine.")


if __name__ == "__main__":
    # parse_alerts_routine()
    notify_chats_routine()
    # delete_past_alerts_routine()
