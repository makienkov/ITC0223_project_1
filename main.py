"""
Global scope
"""
import sys
import logging
import json
import re
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import datetime

USER_AGENT = UserAgent()
CONFIG_FILE_NAME = "conf.json"
LOG_FILE_NAME = "logs.log"
URL = """https://seekingalpha.com/market-news?page="""
SITE_URL = "https://seekingalpha.com"

with open(LOG_FILE_NAME, "wb"):  # clear the log file
    pass
logging.basicConfig(
    filename=LOG_FILE_NAME, level=logging.DEBUG, format="%(levelname)s - %(message)s"
)


def load_config():
    """
    Loading the configuration file and parsing the configuration
    will return the state of debug mode and the number of pages
    to scrape.
    """

    required_constants = ["DEPLOYMENT_NUMBER_OF_PAGES"]
    required_constants.append("DEBUG_LOG_LEVEL")
    required_constants.append("DEPLOYMENT_LOG_LEVEL")
    required_constants.append("DEBUG_MODE")
    required_constants.append("DEBUG_NUMBER_OF_PAGES")
    required_constants.append("DEBUG_NUMBER_OF_URLS")

    try:
        with open(CONFIG_FILE_NAME, "rb") as myfile:
            obj = myfile.read()
            obj = json.loads(obj)

        if set(required_constants).intersection(list(obj.keys())) == set(
            required_constants
        ):
            logging.info("all config parameters loaded successfully from config file")
        else:
            logging.error(
                "Config file does nor contain the one or more required parameters"
            )
            logging.critical("Exiting program...")
            sys.exit()

        debug_log_level = obj["DEBUG_LOG_LEVEL"]
        deployment_log_level = obj["DEPLOYMENT_LOG_LEVEL"]
        debug_mode = obj["DEBUG_MODE"]
        debug_number_of_pages = obj["DEBUG_NUMBER_OF_PAGES"]
        deployment_number_of_pages = obj["DEPLOYMENT_NUMBER_OF_PAGES"]
        debug_number_of_urls = obj["DEBUG_NUMBER_OF_URLS"]

        logging.info("Config file loaded successfully")
    except FileNotFoundError:
        logging.error("Config file not found")
        logging.critical("Exiting program...")
        sys.exit()

    logger = logging.getLogger()  # get the root logger

    if debug_mode:
        logger.setLevel(debug_log_level)
        logging.info("debug mode is: %s", debug_mode)
        logging.info("logging level set to: %s", debug_log_level)
        logging.info("number of pages to scrape is: %s", debug_number_of_pages)
        logging.info("number of URLs to scrape is limited to: %s", debug_number_of_urls)
    else:
        logger.setLevel(deployment_log_level)
        logging.info("debug mode is: %s", debug_mode)
        logging.info("logging level set to: %s", deployment_log_level)
        logging.info("number of pages to scrape is: %s", deployment_number_of_pages)

    logging.info("URL in use is: %s", URL)
    logging.debug("Test debug level")

    if debug_mode:
        number_of_pages = debug_number_of_pages
    else:
        number_of_pages = deployment_number_of_pages
    return debug_mode, number_of_pages, debug_number_of_urls


def url_to_soup(url: str) -> BeautifulSoup:
    """A function that:
    "requests" the HTML page from the given string  - URL,
    and parse it with BeautifulSoup will return the corresponding
    object.
    """
    logging.info("url_to_soup() was called with:\n %s", url)

    try:
        soup = BeautifulSoup(requests.get(url, timeout=10).text, "html.parser")
        logging.info("fetched successfully")
    except FileNotFoundError:
        logging.error("unreachable !")
        logging.critical("Exiting program...")
        sys.exit()

    return soup

def check_percentage(percentage_string):
    """checks for percentage string formatting
    Args:
        percentage_string (string): the string to test
    Returns:
        string: "absent" or the string if in percent formatting
    """
    if percentage_string.startswith("+") or percentage_string.startswith("-") or percentage_string == "0.00":
        return percentage_string
    else:
        return "absent"


def extract_links_and_titles(num_pages):
    """A function that:
    extracts article's links (full and short) from news main page(s).
    Outputs a dict of {title: [full_link, short_link]}

    :param news_page: a url to scrap
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
            price_change_time = "{}/{}/{} {}:{}:{}".format(
                now.year, now.month, now.day, now.hour, now.minute, now.second
            )
            title_data2.append(price_change_time)
            output_dict[title] += title_data2
            logging.info("extracted title: %s with data: %s", "title", title_data2)

    return output_dict


def extract_price_change(soup):
    """A function that:
    extracts current price change from provided soup of article page

    :param soup: the soup of article page

    :return: current price change
    """
    logging.info("extract_price_change() was called")

    # TODO: not implemented yet!
    return None


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

    return [ticker, date_str, time_, author]


def extract_data_from_articles(articles: dict, debug, debug_num_urls):
    """A function that:
    Extracts data about articles and fills it into the provided dict
    :param articles:
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


def main():
    """
    Main function:
    """
    # TODO: need to add grequest usage
    logging.info("Main() started..")

    debug, number, debug_num_urls = load_config()
    print("debug mode is:", debug)
    print("number of pages to scrape is:", number)

    my_dict = extract_links_and_titles(number)

    extract_data_from_articles(my_dict, debug, debug_num_urls)

    for key, value in list(my_dict.items())[:debug_num_urls]:
        print(f"{key}")
        for item in value:
            print(item)
        print("*****************************")


if __name__ == "__main__":
    main()
    logging.info("Main() ended.")
