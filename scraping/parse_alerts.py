import os
import re
import logging
import requests
import arrow
from bs4 import BeautifulSoup
import uuid
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from models import Alert

parsingLogger = logging.getLogger(__name__)
parsingLogger.setLevel(logging.DEBUG)


def take_screenshot_alerts_map():
    """ Take screenshot of the alerts map and store it in the tmp folder """

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
    """ Parse alerts published by INMET.

    Args:
        ignoreModerate: if set to True, will ignore alerts of moderate severity. Defaults to True.

    Return:
        list of alert objects.
    """

    alertsXML = parse_alerts_xml(ignoreModerate)
    alerts = instantiate_alerts_objects(alertsXML, ignoreModerate)
    return alerts


def is_wanted_alert(alertXML, ignoreModerate=True):
    """ Check if alert is wanted - an alert is wanted if endDate has not already passed and the alert isn't moderate if `ignoreModerate` is set to `True`.

    Args:
        alert: the alert's XML parsed from BS4.
        ignoreModerate: if set to True, will ignore alerts of moderate severity. Defaults to True.

    Return:
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
            endDatePattern = r"Fim<\/th><td>(\d{4}-\d{2}-\d{2} \d\d:\d\d:\d\d\.\d)"
            endDateMatch = re.search(endDatePattern, str(alertXML))
            if endDateMatch:
                endDate = arrow.get(endDateMatch.group(1))
                if brazilTime < endDate:
                    return True
                else:
                    return False
            else:
                parsingLogger.error("No match.")


def instantiate_alerts_objects(alertsXML, ignoreModerate=True):
    """ Create and return `list` of `alert` objects from list of alert XMLs

    Args:
        ignoreModerate: if set to True, will ignore alerts of moderate severity. Defaults to True.
    """

    return [Alert(alertXML) for alertXML in alertsXML]


def parse_alerts_xml(ignoreModerate=True):
    """ Parse XMLs from list of XML urls.

    Args:
        ignoreModerate: if set to True, will ignore alerts of moderate severity. Defaults to True.

    Return:
        xmls: list of parsed XMLs.
    """

    xmlURLs = get_alerts_xml(ignoreModerate)

    xmls = []
    for xmlURL in xmlURLs:
        xmls.append(parse_alert_xml(xmlURL))
    parsingLogger.debug("Done parsing XMLs.")
    return xmls


def parse_alert_xml(xmlURL):
    """ Parse alerts XML URL from INMET with BeautifulSoup.

    Args:
        xmlURL: URL to the XML file.
    Return:
        parsed XML or None if GET request to XML URL fails.
    """

    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}

    req = requests.get(xmlURL, headers=headers, allow_redirects=False)
    if req.status_code == 200:
        parsingLogger.info("Successful GET request to alert XML!")

        # Retrieve the XML content
        content = req.content
        alertXML = BeautifulSoup(content, 'xml')
        return alertXML
    else:
        parsingLogger.error("Failed GET request to alert XML.")
        return None


def get_alerts_xml(ignoreModerate=True):
    """ Extract alerts XML URLs from INMET's RSS feed.

    Args:
        ignoreModerate: if set to True, will ignore alerts of moderate severity. Defaults to True.
    Return:
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
        itemsXMLURL = [item.guid.text for item in items if is_wanted_alert(item, ignoreModerate)]

        return itemsXMLURL
    else:
        parsingLogger.error("Failed GET request to alerts RSS.")
        return None


if __name__ == "__main__":
    take_screenshot_alerts_map()
