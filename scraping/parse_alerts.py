import sys
sys.path.append(sys.path[0] + "/..")
import os
import re
import logging
import requests
import arrow
from bs4 import BeautifulSoup
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import models

parsingLogger = logging.getLogger(__name__)
parsingLogger.setLevel(logging.DEBUG)


def take_screenshot_alerts_map():
    """Take screenshot of the alerts map and store it in the tmp folder."""

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=540x1080")

    if 'ON_HEROKU' in os.environ:
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_PATH")
        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)
    else:
        chrome_driver = os.path.join(os.getcwd(), "chromedriver.exe")
        driver = webdriver.Chrome(options=chrome_options, executable_path=chrome_driver)

    driver.get("http://alert-as.inmet.gov.br/cv/")
    parsingLogger.debug(f"Accessed alert-as map.")

    alertsMapPath = os.path.join("tmp", f"alerts_map_{uuid.uuid4().hex}.png")
    driver.find_element_by_id('OpenLayers.Map_3_OpenLayers_ViewPort').screenshot(alertsMapPath)

    return alertsMapPath


def parse_alerts(ignoreModerate=True):
    """Parse alerts published by INMET.

    Parameters
    --------
    ignoreModerate : bool
        If set to True, will ignore alerts of moderate severity. Defaults to True.

    Returns
    --------
    alerts : list : Alert
        List of alert objects.
    """

    alertsXML = parse_alerts_xml(ignoreModerate)
    alerts = instantiate_alerts_objects(alertsXML, ignoreModerate)
    return alerts


def is_wanted_alert(alertXML, ignoreModerate=True):
    """Check if alert is wanted - an alert is wanted if it's not already present in the database, endDate has not already passed and the alert isn't moderate if `ignoreModerate` is set to `True`.

    Parameters
    --------
        alert: the alert's XML parsed from BS4.
        ignoreModerate: if set to True, will ignore alerts of moderate severity. Defaults to True.

    Returns
    --------
        True if alert is wanted, False otherwise.
    """

    brazilTime = arrow.utcnow().to("Brazil/East")

    severityPattern = r"(?<=Severidade Grau: )(.*)(?=<\/title)"
    severityMatch = re.search(severityPattern, str(alertXML))
    if severityMatch:
        severity = severityMatch.group(1)
        if severity == "Perigo Potencial" and ignoreModerate:
            return False
    else:
        parsingLogger.error("No severity match.")

    endDatePattern = r"Fim<\/th><td>(\d{4}-\d{2}-\d{2} \d\d:\d\d:\d\d\.\d)"
    endDateMatch = re.search(endDatePattern, str(alertXML))
    if endDateMatch:
        endDate = arrow.get(endDateMatch.group(1))
        if brazilTime > endDate:
            return False
    else:
        parsingLogger.error("No date match.")

    guidTag = alertXML.find("guid").text
    guidPattern = r"(?<!\/\d\d\/)urn:oid:(.*?)\.xml"
    guidMatch = re.search(guidPattern, str(guidTag))
    if guidMatch:
        alertID = guidMatch.group(1)
        if models.INMETBotDB.alertsCollection.find_one({"alertID": alertID}):
            # parsingLogger.debug("Alert already in database.")
            return False
        else:
            return True
            # parsingLogger.debug("New alert.")
    else:
        parsingLogger.error("No guid match.")


def instantiate_alerts_objects(alertsXML, ignoreModerate=True):
    """Create and return `list` of `alert` objects from list of alert XMLs

    Parameters
    --------
    ignoreModerate : bool
        If set to True, will ignore alerts of moderate severity. Defaults to True.
    """

    return [models.Alert(alertXML) for alertXML in alertsXML]


def parse_alerts_xml(ignoreModerate=True):
    """Parse XMLs from list of XML urls.

    Parameters
    --------
    ignoreModerate : bool
        If set to True, will ignore alerts of moderate severity. Defaults to True.

    Returns
    --------
    xmls : list : BeautifulSoup
        list of parsed XMLs.
    """

    xmlURLs = get_alerts_xml(ignoreModerate)
    xmls = [parse_alert_xml(xmlURL) for xmlURL in xmlURLs]
    parsingLogger.debug("Done parsing XMLs.")
    return xmls


def parse_alert_xml(xmlURL):
    """Parse alerts XML URL from INMET with BeautifulSoup.

    Parameters
    --------
    xmlURL : str
        URL to the XML file.

    Returns
    --------
    parsedAlertXML : BeautifulSoup
        parsed XML or None if GET request to XML URL fails.
    """

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(xmlURL, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        parsingLogger.info("Successful GET request to alert XML!")

        # Retrieve the XML content
        content = req.content
        parsedAlertXML = BeautifulSoup(content, 'xml')
        return parsedAlertXML
    else:
        parsingLogger.error("Failed GET request to alert XML.")
        return None


def get_alerts_xml(ignoreModerate=True):
    """Extract alerts XML URLs from INMET's RSS feed.

    Parameters
    --------
    ignoreModerate : bool
        If set to True, will ignore alerts of moderate severity. Defaults to True.

    Returns
    --------
    itemsXMLURL : list : str
        List of all available XML URLs for alerts.
    """

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    alertsURL = "https://alerts.inmet.gov.br/cap_12/rss/alert-as.rss"
    req = requests.get(alertsURL, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        parsingLogger.info("Successful GET request to alerts RSS!")

        # Retrieve the RSS feed content
        content = req.content
        xml = BeautifulSoup(content, 'html.parser')
        # parsingLogger.debug(xml)

        # Get alerts' XML URL from each item entry
        items = xml.channel.find_all("item")
        itemsXMLURLs = [item.guid.text for item in items if is_wanted_alert(item, ignoreModerate)]

        return itemsXMLURLs
    else:
        parsingLogger.error("Failed GET request to alerts RSS.")
        return None


if __name__ == "__main__":
    take_screenshot_alerts_map()
