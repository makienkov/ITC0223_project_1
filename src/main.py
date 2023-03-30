"""
Global scope
"""
import sys
import time
import datetime
import logging
import json
import requests
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent

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
        logging.info(
            "number of pages to scrape is limited to: %s", debug_number_of_pages
        )
    else:
        logger.setLevel(deployment_log_level)
        logging.info("debug mode is: %s", debug_mode)
        logging.info("logging level set to: %s", deployment_log_level)
        logging.info(
            "number of pages to scrape is limited to: %s", deployment_number_of_pages
        )

    logging.info("URL in use is: %s", URL)
    logging.debug("Test debug level")

    if debug_mode:
        mode = debug_mode
        number_of_pages = debug_number_of_pages
    else:
        mode = debug_mode
        number_of_pages = deployment_number_of_pages
    return mode, number_of_pages


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

    # TODO: need to add grequest usage
    return soup


def soup_symbols_to_data(soup: BeautifulSoup):
    """A function that:
    given BeautifulSoup object - 1 web page content with all news,
    parse it and will create a list for each title with the:
    [title, symbol, time1, prise_delta, origin_url, author, time2]
    and return the list
    """
    logging.info("soup_to_titles_list() was called")

    ans = []

    for article in soup.select('article[data-test-id="post-list-item"]'):
        article_title = soup.select_one("h3").text
        print(article_title)

        corrected_article_title = " ".join(article_title.split())

        link = article.select_one('a[href^="/news/"]')["href"]
        substring = link.split("/")[-1].split("?")[0]
        href = "https://seekingalpha.com/news/" + substring

        substring = substring.split("-")
        article_id = substring[0]

        ans.append([corrected_article_title, article_id, href])

    return ans


def extract_price_change(soup):
    """A function that:
    extracts current price change from provided soup of article page

    :param soup: the soup of article page

    :return: current price change
    """
    # TODO: not implemented yet!
    return None


def extract_data_from_soup(soup):
    """A function that:
    extracts data from soup of article page
    and returns the dictionary of single item in the following format:
    title: [ticker, date_str, time, author, data]

    :param soup:
    :return:
    """

    text = soup.text

    data = " ".join(text.split("\n")[2:-1])
    logging.info(data)

    match = re.search(r"\((\w+)\)By:", text)
    if match:
        ticker = match.group(1)
        logging.info(ticker)
    else:
        ticker = None
        logging.critical("ticker not found.")

    match = re.search(r"By:\s+(\w+\s*)+", text)
    if match:
        author = match.group(0).replace("By: ", "").strip()
        logging.info(author)
    else:
        author = None
        logging.critical("Author not found.")

    match = re.search(r'\w{3}\. \d{1,2}, \d{4}', text)
    if match:
        date_str = match.group()
        logging.info(date_str)
    else:
        date_str = None
        logging.critical("Date not found.")

    match = re.search(r'\d{1,2}:\d{2} [AP]M', text)
    if match:
        time = match.group()
        logging.info(time)
    else:
        time = None
        logging.critical("time not found.")

    match = re.search(r"(.+?) \|", text)
    if match:
        title = match.group()[:-2]
        logging.info(title)
    else:
        title = None
        logging.critical("title not found.")

    ans = [title, ticker, date_str, time, author, data]
    # TODO: often fails to find staff (read critical debug)

    return ans


def extract_links_and_titles(news_page: str = URL, num_pages=1):
    """A function that:
    extracts article's links (full and short) from news main page(s).
    Outputs a dict of {title: [full_link, short_link]}

    :param news_page: a url to scrap
    :return: a dict of {title: link}
    """
    output_dict = {}

    for i in range(1, num_pages + 1):
        url = news_page + str(i)

        link_soup = url_to_soup(url)

        selects = link_soup.select('article div div h3 a')

        for select in selects:
            href = select.attrs.get('href')
            output_dict[select.text] = [
                SITE_URL + href[:href.find('?')],  # full link
                SITE_URL + href[:13]  # short link
            ]

    return output_dict


def extract_data_from_articles(articles: dict):
    """A function that:
    Extracts data about articles and fills it into the provided dict
    :param articles:
    """
    for title, values in articles.items():
        articles[title] += extract_data_from_soup(
            url_to_soup(values[0])
        )


def data_mining(news_page: str = URL, num_pages=1):
    """A function that:
    scraps main page and then articles' subpages
    and returns the main dictionaty of the project

    :param news_page: a link to news page on seeking alpha
    :param num_pages: a number of pages to scrap
    :return:
    """
    output = extract_links_and_titles(news_page, num_pages)
    extract_data_from_articles(output)

    return output


def data_mining_test(num_pages=2, articles_show=3):
    i = 1
    for key, value in data_mining(num_pages=num_pages).items():
        if i > articles_show:
            break

        i += 1
        print(f'{key} :\n'
              f' {value[0]}\n'
              f' {value[1]}\n'
              f' {value[2]}\n'
              f' {value[3:-1]}\n'
              f' {value[-1]}\n')

    print('}')


def time_some_function(function_, args_list: list) -> str:
    """A function that:
    given the function name and the list of arguments,
    will execute the function and return the result
    in string format the time it took to execute the function.
    in the following format: 0:00:37.183115 = Hours:Minutes:Seconds.milliseconds
    """
    logging.info("time_some_function() was called for %s", function_)

    start_time = time.time()
    function_(*args_list)
    end_time = time.time()
    time_taken = end_time - start_time
    return str(datetime.timedelta(seconds=time_taken))


def main():
    """
    Main function:
    """
    logging.info("main() started")

    debug, number = load_config()
    print("debug mode is:", debug)
    print("number of pages to scrape is:", number)

    data_mining_test(num_pages=2, articles_show=3)


if __name__ == "__main__":
    main()
