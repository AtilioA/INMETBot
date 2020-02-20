import logging
import parse_alerts
import models
import pycep_correios as pycep
from bot_config import updater
import bot_utils

routinesLogger = logging.getLogger(__name__)
routinesLogger.setLevel(logging.DEBUG)


def parse_alerts_routine(ignoreModerate=False):
    """ Parse alerts published by INMET and insert into database.

    Args:
        ignoreModerate: if set to True, will ignore alerts of moderate severity. Defaults to True.

    Return:
        True if successful, False otherwise
    """

    alertsXML = parse_alerts.parse_alerts_xml(ignoreModerate)
    alerts = parse_alerts.instantiate_alerts_objects(alertsXML, ignoreModerate)
    routinesLogger.debug(alerts)
    for alert in alerts:
        models.insert_alert(alert)
    return True  # ?!


def notify_chats_routine():
    subscribedChats = list(models.subscribedChatsCollection.find({}))
    alerts = list(models.alertsCollection.find({}))

    for chat in subscribedChats:
        routinesLogger.debug(f"Checking chat {chat['chatID']}")
        for alert in alerts:
            if chat["chatID"] not in alert["notifiedChats"]:
                # routinesLogger.debug(f"Chat {chat['chatID']} has not been notified yet.")
                for cep in chat["CEPs"]:
                    try:
                        cepJSON = pycep.consultar_cep(cep)
                        city = cepJSON["cidade"]
                        routinesLogger.debug(f"Checking {city}...")
                    except Exception as error:
                        print(error)
                    else:
                        if city in alert["cities"]:
                            routinesLogger.debug(f"Notifying chat {chat['chatID']}...")
                            alertMessage = bot_utils.get_alert_message_dict(alert, city)
                            alertMessage += "\nVeja os gráficos em http://www.inmet.gov.br/portal/alert-as/"
                            updater.bot.send_message(chat_id=chat["chatID"], text=alertMessage, parse_mode="markdown", disable_web_page_preview=True)
                            models.alertsCollection.update({"alertID": alert["alertID"]}, {"$addToSet": {"notifiedChats": chat['chatID']}})


if __name__ == "__main__":
    # parse_alerts_routine()
    notify_chats_routine()
    pass
