import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup


class Alert():
    def __init__(self, item=None):
        if item:
            self.get_event(item)
            self.get_severity(item)
            self.get_startDate(item)
            self.get_endDate(item)
            self.get_description(item)
            self.get_area(item)
            self.get_graphURL(item)
        else:
            self.event = ""
            self.severity = ""
            self.startDate = ""
            self.endDate = ""
            self.description = ""
            self.area = ""
            self.graphURL = ""

    def get_event(self, item):
        eventPattern = r"<title>(.*?)(?= Severidade)"  # "event" is same as "title"
        eventMatch = re.search(eventPattern, str(item))
        if eventMatch:
            self.event = eventMatch.group(1)

    def get_severity(self, item):
        severityPattern = r"(?<=Severidade Grau: )(.*?)(?=</title)"
        severityMatch = re.search(severityPattern, str(item))
        if severityMatch:
            self.severity = severityMatch.group(1)

    def get_description(self, item):
        descriptionPattern = r"Descrição</th><td>INMET publica aviso iniciando em: .*?\. (.*?)(?=</td>)"
        descriptionMatch = re.search(descriptionPattern, str(item))
        if descriptionMatch:
            self.description = descriptionMatch.group(1)

    def get_area(self, item):
        areaPattern = r"(?<=Aviso para as áreas: )(.*?)(?=</td>)"
        areaMatch = re.search(areaPattern, str(item))
        if areaMatch:
            self.area = areaMatch.group(1).split(",")

    def get_graphURL(self, item):
        graphURLPattern = r"Link Gráfico</th><td><a href=\"(.*?)\""
        graphURLMatch = re.search(graphURLPattern, str(item))
        if graphURLMatch:
            self.graphURL = graphURLMatch.group(1)

    def get_startDate(self, item):
        startDatePattern = r"Início<\/th><td>(\d{4}-\d{2}-\d{2} \d\d:\d\d:\d\d\.\d)"
        startDateMatch = re.search(startDatePattern, str(item))
        if startDateMatch:
            self.startDate = datetime.strptime(startDateMatch.group(1), '%Y-%m-%d %H:%M:%S.%f')

    def get_endDate(self, item):
        endDatePattern = r"Fim<\/th><td>(\d{4}-\d{2}-\d{2} \d\d:\d\d:\d\d\.\d)"
        endDateMatch = re.search(endDatePattern, str(item))
        if endDateMatch:
            self.endDate = datetime.strptime(endDateMatch.group(1), '%Y-%m-%d %H:%M:%S.%f')


def get_alerts_objects(items):
    alertsObjects = []
    dateNow = datetime.now()
    for item in items:
        alert = Alert(item)
        if (alert.endDate > dateNow) and (alert.severity != "Perigo Potencial"):
            alertsObjects.append(alert)

    return alertsObjects


def parse_alerts():
    """ Extract Danger/Great Danger alerts from INMET's RSS feed """

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    alertsURL = "https://alerts.inmet.gov.br/cap_12/rss/alert-as.rss"
    req = requests.get(alertsURL, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        print("Successful GET request to alerts RSS!")

        # Retrieve the RSS feed content
        content = req.content
        xml = BeautifulSoup(content, 'html.parser')

        # Get alerts from each item entry
        items = xml.channel.find_all("item")
        alerts = get_alerts_objects(items)

        # print(len(alerts))
        return alerts
    else:
        print("Failed GET request to alerts RSS.")


if __name__ == "__main__":
    parse_alerts()
