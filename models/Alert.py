import logging
import arrow
import re
from db import INMETBotDB

modelsLogger = logging.getLogger(__name__)
modelsLogger.setLevel(logging.DEBUG)


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

    def set_id_from_XML(self, alertXML):
        """Extract id string from XML."""

        alertID = alertXML.identifier.text.replace("urn:oid:", "")
        self.id = alertID

    def set_event_from_XML(self, alertXML):
        """Extract event string from XML."""

        eventPattern = r"(.*?)(?= Severidade)"
        rawEvent = alertXML.info.headline.text
        eventMatch = re.search(eventPattern, rawEvent)
        if eventMatch:
            self.event = eventMatch.group(1)

    def set_severity_from_XML(self, alertXML):
        """Extract severity string from XML."""

        rawSeverity = alertXML.info.headline.text
        severityPattern = r"(?<=Severidade Grau: )(.*)"
        severityMatch = re.search(severityPattern, rawSeverity)
        if severityMatch:
            self.severity = severityMatch.group(1)

    def set_description_from_XML(self, alertXML):
        """Extract description string from XML."""

        rawDescription = alertXML.info.description.text
        descriptionPattern = r"INMET publica aviso iniciando em: .*?\. (.*)"
        descriptionMatch = re.search(descriptionPattern, rawDescription)
        if descriptionMatch:
            self.description = descriptionMatch.group(1)

    def set_area_from_XML(self, alertXML):
        """Extract area string from XML, process it and put it in a list."""

        rawArea = alertXML.info.area.areaDesc.text
        areaPattern = r"(?<=Aviso para as áreas: )(.*)"
        areaMatch = re.search(areaPattern, rawArea)
        if areaMatch:
            self.area = [region for region in areaMatch.group(1).split(",")]

    def set_cities_from_XML(self, alertXML):
        """Extract cities string from XML, process it and put it in a list."""

        parameters = alertXML.info.find_all("parameter")
        citiesParameter = None
        for parameter in parameters:
            if "Municipio" in parameter.valueName.text:
                citiesParameter = parameter
        rawCities = citiesParameter.value.text.split(",")
        cities = [re.sub(r"\s\-.*?\)", "", city).strip() for city in rawCities]
        self.cities = cities

    def set_startDate_from_XML(self, alertXML):
        """Extract startDate string from XML (convert to arrow Object)."""

        startDate = arrow.get(str(alertXML.info.onset.text))
        self.startDate = startDate

    def set_endDate_from_XML(self, alertXML):
        """Extract endDate string from XML (convert to arrow Object)."""

        endDate = arrow.get(str(alertXML.info.expires.text))
        self.endDate = endDate


if __name__ == "__main__":
    pass
