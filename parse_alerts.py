from models import Alert
import re
import requests
import arrow
from bs4 import BeautifulSoup


BRAZIL_TIME = arrow.utcnow().to("Brazil/East")


def parse_alerts(ignoreModerate=True):
    alertsXML = parse_alerts_xml(ignoreModerate)
    alerts = instantiate_alerts_objects(alertsXML, ignoreModerate)
    return alerts


def is_wanted_alert(item, ignoreModerate=True):
    severityPattern = r"(?<=Severidade Grau: )(.*)(?=<\/title)"
    severityMatch = re.search(severityPattern, str(item))
    if severityMatch:
        severity = severityMatch.group(1)
        if severity == "Perigo Potencial" and ignoreModerate:
            return False
        else:
            endDatePattern = r"Fim<\/th><td>(\d{4}-\d{2}-\d{2} \d\d:\d\d:\d\d\.\d)"
            endDateMatch = re.search(endDatePattern, str(item))
            if endDateMatch:
                endDate = arrow.get(endDateMatch.group(1))
                if BRAZIL_TIME < endDate:
                    return True
                else:
                    return False
            else:
                print("No match.")


def instantiate_alerts_objects(alertsXML, ignoreModerate=True):
    return [Alert(alertXML) for alertXML in alertsXML]


def parse_alerts_xml(ignoreModerate=True):
    xmlURLs = get_alerts_xml(ignoreModerate)

    xmls = []
    for xmlURL in xmlURLs:
        xmls.append(parse_alert_xml(xmlURL))
    return xmls


def parse_alert_xml(xmlURL=""):
    """ Parse alerts XML URL from INMET. """

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(xmlURL, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        print("Successful GET request to alert XML!")

        # Retrieve the XML content
        content = req.content
        alertXML = BeautifulSoup(content, 'xml')
        return alertXML
    else:
        print("Failed GET request to alert XML.")
        return None


def get_alerts_xml(ignoreModerate=True):
    """ Extract alerts XML URLs from INMET's RSS feed. """

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    alertsURL = "https://alerts.inmet.gov.br/cap_12/rss/alert-as.rss"
    req = requests.get(alertsURL, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        print("Successful GET request to alerts RSS!")

        # Retrieve the RSS feed content
        content = req.content
        xml = BeautifulSoup(content, 'html.parser')
        # print(xml)

        # Get alerts' XML URL from each item entry
        items = xml.channel.find_all("item")
        itemsXMLURL = [item.guid.text for item in items if is_wanted_alert(item, ignoreModerate)]

        return itemsXMLURL
    else:
        print("Failed GET request to alerts RSS.")
        return None


if __name__ == "__main__":
    alerts = parse_alerts(ignoreModerate=False)
    # print(len(alerts))
    # for alert in alerts:
        # print(alert.area)
