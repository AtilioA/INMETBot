import arrow
import re

class Alert():
    def __init__(self, alertXML=None):
        """ Carry information about an alert (reads from XML file). """

        if alertXML:
            self.get_event_from_XML(alertXML)
            self.get_severity_from_XML(alertXML)
            self.get_startDate_from_XML(alertXML)
            self.get_endDate_from_XML(alertXML)
            self.get_description_from_XML(alertXML)
            self.get_area_from_XML(alertXML)
            self.get_cities_from_XML(alertXML)
        else:
            self.event = ""
            self.severity = ""
            self.startDate = ""
            self.endDate = ""
            self.description = ""
            self.area = ""
            self.cities = ""
        self.graphURL = "http://www.inmet.gov.br/portal/alert-as/"

    def get_event_from_XML(self, alertXML):
        """ Extract event string from XML. """

        eventPattern = r"(.*?)(?= Severidade)"
        rawEvent = alertXML.info.headline.text
        eventMatch = re.search(eventPattern, rawEvent)
        if eventMatch:
            self.event = eventMatch.group(1)

    def get_severity_from_XML(self, alertXML):
        """ Extract severity string from XML. """

        rawSeverity = alertXML.info.headline.text
        severityPattern = r"(?<=Severidade Grau: )(.*)"
        severityMatch = re.search(severityPattern, rawSeverity)
        if severityMatch:
            self.severity = severityMatch.group(1)

    def get_description_from_XML(self, alertXML):
        """ Extract description string from XML. """

        rawDescription = alertXML.info.description.text
        descriptionPattern = r"INMET publica aviso iniciando em: .*?\. (.*)"
        descriptionMatch = re.search(descriptionPattern, rawDescription)
        if descriptionMatch:
            self.description = descriptionMatch.group(1)

    def get_area_from_XML(self, alertXML):
        """ Extract area string from XML, process it and put it in a list. """

        rawArea = alertXML.info.area.areaDesc.text
        areaPattern = r"(?<=Aviso para as áreas: )(.*)"
        areaMatch = re.search(areaPattern, rawArea)
        if areaMatch:
            self.area = [region for region in areaMatch.group(1).split(",")]

    def get_cities_from_XML(self, alertXML):
        """ Extract cities string from XML, process it and put it in a list """

        parameters = alertXML.info.find_all("parameter")
        citiesParameter = None
        for parameter in parameters:
            if "Municipio" in parameter.valueName.text:
                citiesParameter = parameter
        rawCities = citiesParameter.value.text.split(',')
        cities = [re.sub(r"\s\-.*?\)", '', city).strip() for city in rawCities]
        self.cities = cities

    def get_startDate_from_XML(self, alertXML):
        """ Extract startDate string from XML (convert to arrow Object). """

        startDate = arrow.get(str(alertXML.info.onset.text))
        self.startDate = startDate

    def get_endDate_from_XML(self, alertXML):
        """ Extract endDate string from XML (convert to arrow Object). """

        endDate = arrow.get(str(alertXML.info.expires.text))
        self.endDate = endDate
