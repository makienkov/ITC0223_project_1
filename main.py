"""
!/usr/bin/env python3
----------------------------------------------------------------
Global scope
----------------------------------------------------------------
"""
import time
import sys
import logging
import json
import re
import datetime
import requests
from bs4 import BeautifulSoup

LOG_FILE_NAME = ".".join(__file__.split(".")[:-1]) + ".log"
CONFIG_FILE_NAME = "conf.json"

with open(LOG_FILE_NAME, "wb"):
    pass

logging.basicConfig(
    filename=LOG_FILE_NAME,
    level=logging.DEBUG,
    format="%(levelname)s - %(asctime)s - %(message)s",
)


def load_config():
    """
    Loads the configuration file settings "conf.json".
    Returns the global parameters
    """
    logging.info("load_config() started")

    required_constants = [
        "DEBUG_MODE",
        "DEBUG_LOG_LEVEL",
        "DEPLOYMENT_LOG_LEVEL",
        "URL",
        "DEBUG_NUMBER_OF_PAGES",
        "DEBUG_NUMBER_OF_URLS",
        "DEPLOYMENT_NUMBER_OF_PAGES",
    ]

    try:
        with open("conf.json", "rb") as my_file:
            obj = my_file.read()
            obj = json.loads(obj)

        if set(required_constants).intersection(list(obj.keys())) == set(
            required_constants
        ):
            logging.info("all config parameters loaded successfully from config file")
        else:
            logging.error(
                "Config file does not contain the one or more required parameters"
            )
            logging.critical("Exiting program...")
            sys.exit()

        logging.info("Config file loaded successfully")
    except FileNotFoundError:
        logging.error("Config file not found")
        logging.critical("Exiting program...")
        sys.exit()

    debug_mode_ = obj["DEBUG_MODE"]
    debug_log_level_ = obj["DEBUG_LOG_LEVEL"]
    deployment_log_level_ = obj["DEPLOYMENT_LOG_LEVEL"]
    url_ = obj["URL"]
    site_url_ = "/".join(url_.split("/")[0:-1])
    debug_number_of_urls_ = obj["DEBUG_NUMBER_OF_URLS"]
    deployment_number_of_pages_ = obj["DEPLOYMENT_NUMBER_OF_PAGES"]
    debug_number_of_pages_ = obj["DEBUG_NUMBER_OF_PAGES"]

    if debug_mode_:
        number_of_pages = debug_number_of_pages_
    else:
        number_of_pages = deployment_number_of_pages_

    logging.info("debug mode is: %s", debug_mode_)
    logging.info("debug log level is: %s", debug_log_level_)
    logging.info("deployment log level  is: %s", deployment_log_level_)
    logging.info("URL is: %s", url_)
    logging.info("site URL is: %s", site_url_)
    logging.info("debug number of urls_ is: %s", debug_number_of_urls_)
    logging.info("number of pages is: %s", number_of_pages)

    logging.info("load_config() completed")

    return [
        debug_mode_,
        debug_log_level_,
        deployment_log_level_,
        url_,
        site_url_,
        debug_number_of_urls_,
        number_of_pages,
    ]


glob = load_config()
DEBUG_MODE = glob[0]
DEBUG_LOG_LEVEL = glob[1]
DEPLOYMENT_LOG_LEVEL = glob[2]
URL = glob[3]
SITE_URL = glob[4]
DEBUG_NUMBER_OF_URLS = glob[5]
NUMBER_OF_PAGES = glob[6]
del glob


def set_log_level():
    """
    Change the logging level according
    to the DEBUG_MODE variable
    """

    logging.info("load_logs() started")

    error_map = {
        10: "DEBUG=10",
        20: "INFO=20",
        30: "WARN=30",
        40: "ERROR=40",
        50: "CRITICAL=50",
    }

    # set logger level
    if DEBUG_MODE:
        level_ = DEBUG_LOG_LEVEL
        logging.info("logging level set to: %s", error_map.get(DEBUG_LOG_LEVEL))
    else:
        level_ = DEPLOYMENT_LOG_LEVEL
        logging.info("logging level set to: %s", error_map.get(DEPLOYMENT_LOG_LEVEL))

    logger = logging.getLogger()
    logger.setLevel(level_)

    logging.info("load_logs() completed")


def url_request(url: str) -> str:
    """A function that:
    "requests" the HTML page from the given string  - URL,
    and will return the HTML page
    """
    logging.info("url_request() was called with:\n %s", url)

    time.sleep(0.1)

    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) \
            Gecko/20100101 Firefox/66.0",
        "Accept-Encoding": "*",
        "Connection": "keep-alive",
    }

    try:
        response = requests.get(url, headers=header, timeout=9.9)
        response.raise_for_status()
        logging.info("connected to server successfully")
    except requests.exceptions.HTTPError as error:
        print(f"An error occurred: {error}")
        logging.error("server unreachable !%s", error)
        logging.critical("Exiting program...")
        sys.exit()

    if response.status_code != 200:
        print(f"Request failed with status code: {response.status_code}")
        logging.error("Request failed with status code: %s", response.status_code)
        print("closing program")
        logging.error("closing program")
        sys.exit()
    else:
        logging.info("Request fetched successfully, code=200")
        logging.info("url_request() was ended")
        return response.text


def url_to_soup(url: str) -> BeautifulSoup:
    """A function that:
    "requests" the HTML page from the given string  - URL,
    and parse it with BeautifulSoup will return the corresponding
    object.
    """
    logging.info("url_to_soup() was called with:\n %s", url)

    html = url_request(url)

    soup = BeautifulSoup(html, "html.parser")

    logging.info("url_to_soup() ended")

    return soup


def check_percentage(percentage_string):
    """checks for percentage string formatting
    Args:
        percentage_string (string): the string to test
    Returns:
        string: "absent" or the string if in percent formatting
    """
    logging.info("check_percentage() was called with:\n %s", percentage_string)

    if (
        percentage_string.startswith("+")
        or percentage_string.startswith("-")
        or percentage_string == "0.00"
    ):
        logging.info("check_percentage() was ended")
        return percentage_string

    logging.info("check_percentage() got 'absent' and ended")
    return "absent"


def extract_links_and_titles(num_pages):
    """A function that:
    extracts article's links (full and short) from news main page(s).
    Outputs a dict of {title: [full_link, short_link]}

    :param num_pages: number of pages to scrap
    :return: a dict of {title: link}
    """
    logging.info("extract_links_and_titles() was called with:\n %s", num_pages)

    output_dict = {}

    for i in range(1, num_pages + 1):
        url = URL + str(i)

        link_soup = url_to_soup(url)

        select_object = link_soup.select("article div div h3 a")
        select_object2 = link_soup.select("article div div footer")

        for data, data2 in zip(select_object, select_object2):
            title_data = []
            title = data.text
            href = data.attrs.get("href")
            href = SITE_URL + href[: href.find("?")]
            title_data.append(href)
            title_id = re.search(r"\d+", href).group()
            title_data.append(title_id)
            output_dict[title] = title_data
            logging.info("extracted title: %s with data: %s", title, title_data)

            title_data2 = []
            clean_text = re.sub(r"\s*\d+\s*Comments?", "", data2.text)
            clean_text = clean_text.split()[1:]
            price_change = str(clean_text[0].split("%")[0]) + "%"
            price_change = check_percentage(price_change)
            title_data2.append(price_change)
            now = datetime.datetime.now()
            price_change_time = (
                f"{now.year}/{now.month}/{now.day} {now.hour}:{now.minute}:{now.second}"
            )
            title_data2.append(price_change_time)
            output_dict[title] += title_data2
            logging.info("extracted title: %s with data: %s", "title", title_data2)

    logging.info("extract_links_and_titles() was ended")
    return output_dict


def extract_data_from_soup(soup):
    """A function that:
    extracts data from soup of article page
    and returns the dictionary of single item in the following format:
    title: [ticker, date_str, time, author, data]
    """

    text = soup.text

    logging.info("extract_data_from_soup() was called for %s", text[:100])

    match = re.search(r"\((\w+)\)", text)
    if match:
        ticker = match.group(1)
        logging.info("ticker added ! %s", ticker)
    else:
        ticker = None
        logging.info("ticker not found !! %s", ticker)

    match = re.search(r"By:\s+(\w+\s*)+", text)
    if match:
        author = match.group(0).replace("By: ", "").strip()
        logging.info("author added ! %s", author)
    else:
        author = None
        logging.info("author not found !! %s", author)

    match = re.search(r"\w{3}\. \d{1,2}, \d{4}", text)
    if match:
        date_str = match.group()
        logging.info("date_str added ! %s", date_str)
    else:
        date_str = None
        logging.info("date_str not found !! %s", date_str)

    match = re.search(r"\d{1,2}:\d{2} [AP]M", text)
    if match:
        time_ = match.group()
        logging.info("time_ added ! %s", time_)
    else:
        time_ = None
        logging.info("time_ not found !! %s", time_)

    logging.info("extract_data_from_soup() was ended")
    return [ticker, date_str, time_, author]


def extract_data_from_articles(articles: dict, debug, debug_num_urls):
    """A function that:
    Extracts data about articles and fills it into the provided dict
    """
    logging.info(
        "extract_data_from_articles() was called for # of articles %s", len(articles)
    )

    if debug:
        for title, values in list(articles.items())[:debug_num_urls]:
            articles[title] += extract_data_from_soup(url_to_soup(values[0]))
    else:
        for title, values in articles.items():
            articles[title] += extract_data_from_soup(url_to_soup(values[0]))

    logging.info("extract_data_from_articles() was ended")


def main():
    """
    Main function:
    """
    logging.info("main() started")

    logging.debug("DEBUG before set_log_level()")
    set_log_level()
    logging.debug("DEBUG after set_log_level()")

    print("debug mode is:", DEBUG_MODE)
    print("number of pages to scrape is:", NUMBER_OF_PAGES)

    my_dict = extract_links_and_titles(NUMBER_OF_PAGES)

    extract_data_from_articles(my_dict, DEBUG_MODE, DEBUG_NUMBER_OF_URLS)

    for key, value in list(my_dict.items())[:DEBUG_NUMBER_OF_URLS]:
        print(f"{key}")
        for item in value:
            print(item)
        print("*****************************")

    logging.info("main() completed")


if __name__ == "__main__":
    main()
