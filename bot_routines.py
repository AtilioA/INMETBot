import arrow
import logging
import parse_alerts
import models
# import pycep_correios as pycep
import viacep
from bot_config import updater
import bot_utils

routinesLogger = logging.getLogger(__name__)
routinesLogger.setLevel(logging.DEBUG)


def delete_past_alerts_routine():
    """ Delete past alerts published by INMET from the database. """

    alerts = list(models.alertsCollection.find({}))
    timeNow = arrow.utcnow().to("Brazil/East")
    for alert in alerts:
        if timeNow > arrow.get(alert["endDate"]):
            routinesLogger.info(f"alert {alert['alertID']} is past and will be deleted.")
            models.alertsCollection.delete_one({"alertID": alert["alertID"]})
    routinesLogger.info("Finished delete_past_alerts_routine routine.")


def parse_alerts_routine(ignoreModerate=False):
    """ Parse alerts published by INMET and insert them into database.

    Args:
        ignoreModerate: if set to True, will ignore alerts of moderate severity. Defaults to False.
    """

    alertsXML = parse_alerts.parse_alerts_xml(ignoreModerate)
    alerts = parse_alerts.instantiate_alerts_objects(alertsXML, ignoreModerate)
    routinesLogger.debug(alerts)
    for alert in alerts:
        models.insert_alert(alert)
    routinesLogger.info("Finished parsed_alerts_routine routine.")


def notify_chats_routine():
    """ Check alerts from the database and notify chats.

    For every alert and chat, check if chat has been notified for that alert; if it has not, check if there is any city (obtained by CEPs in the chat's CEP list) that is included in the alert.
    If there is, notify chat and mark chat as notified (so it won't get notified again for the same alert).
    """

    subscribedChats = list(models.subscribedChatsCollection.find({}))
    alerts = list(models.alertsCollection.find({}))

    for chat in subscribedChats:
        routinesLogger.debug(f"Checking chat {chat['chatID']}")
        for alert in alerts:
            if chat["chatID"] not in alert["notifiedChats"]:
                warnedCities = []
                for cep in chat["CEPs"]:
                    try:
                        city = viacep.get_cep_city(cep)
                        routinesLogger.debug(f"Checking {city}...")
                        if city in alert["cities"]:
                            warnedCities.append(city)
                            routinesLogger.info(f"Appended warned city.-")
                    except Exception as error:
                        routinesLogger.error(error)

                if warnedCities:
                    alertObj = models.Alert(alertDict=alert)
                    routinesLogger.info(f"-- Notifying chat {chat['chatID']} for alert {alert['alertID']}... --")

                    alertMessage = bot_utils.get_alert_message(alertObj, warnedCities)
                    alertMessage += "\nVeja os gráficos em http://www.inmet.gov.br/portal/alert-as/"

                    updater.bot.send_message(chat_id=chat["chatID"], text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)
                    models.alertsCollection.update_one({"alertID": alert["alertID"]}, {"$addToSet": {"notifiedChats": chat['chatID']}})

    routinesLogger.info("Finished notify_chats_routine routine.")


if __name__ == "__main__":
    # parse_alerts_routine()
    notify_chats_routine()
    # delete_past_alerts_routine()
    pass
