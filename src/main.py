"""
!/usr/bin/env python3
coding=utf-8
----------------------------------------------------------------
Global scope
----------------------------------------------------------------
"""
import string
import time
import sys
import logging
import json
import re
import argparse
from datetime import datetime
from datetime import timedelta
import grequests
import requests
from bs4 import BeautifulSoup, Tag
import pytz
import mysql.connector
from prettytable import PrettyTable
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm

FILE_NAME = ".".join(__file__.split(".")[:-1])

REQUIRED_CONSTANTS = [
    "DEBUG_MODE",
    "DEBUG_LOG_LEVEL",
    "DEPLOYMENT_LOG_LEVEL",
    "URL",
    "DEBUG_NUMBER_OF_PAGES",
    "DEBUG_NUMBER_OF_URLS",
    "DEPLOYMENT_NUMBER_OF_PAGES",
    "PARALLEL",
    "CHROME_DRIVER_PATH",
    "MYSQL_CONFIG_FILE",
    "SECONDARY_PAGES_SCRAPPING",
    "REQUEST_API_DATA",
    "API_KEY",
    "API_BASE_URL",
    "API_DATA_INTERVAL"
]


def initialise_parser() -> argparse.ArgumentParser:
    """
    The function initializes and returns the parser of CLI user input.

    :return: argparse.ArgumentParser, initialized parser object
    """
    print("initialise_parser() started")
    parser = argparse.ArgumentParser(
        description='Scrap info from "seeking alpha" site and alphavantage.co API')
    parser.add_argument(
        "-c",
        "--config-file",
        type=str,
        default="conf.json",
        help="Path to the .json config file to use",
    )
    parser.add_argument(
        "-l", "--log-file", type=str, default=FILE_NAME + ".log", help="Name of log file"
    )

    parser.add_argument(
        "--debug-log-level",
        type=int,
        choices=[10, 20, 30, 40, 50],
        help="Log level in debug mode, integer."
             "\nPossible choices:"
             "\n* DEBUG=10"
             "\n* INFO=20"
             "\n* WARN=30"
             "\n* ERROR=40"
             "\n* CRITICAL=50",
    )

    parser.add_argument(
        "--deployment-log-level",
        type=int,
        choices=[10, 20, 30, 40, 50],
        help="Log level in deployment mode, integer."
             "\nPossible choices:"
             "\n* DEBUG=10"
             "\n* INFO=20"
             "\n* WARN=30"
             "\n* ERROR=40"
             "\n* CRITICAL=50",
    )

    parser.add_argument(
        "-d",
        "--debug-mode",
        type=bool,
        help="Switcher between dev (debug) and prod (deployment) scenarios.",
    )
    parser.add_argument(
        "--url", type=str, help="URL of the main news page. Must ends with '?page='"
    )
    parser.add_argument(
        "--chrome-driver-path", type=str, help="Path to Google Chrome driver file."
    )
    parser.add_argument(
        "--mysql-config-file", type=str, help="Path to mysql configuration file"
                                              "containing SQL commands and your login and password."
    )
    parser.add_argument(
        "--api-key", type=str, help="API key to request data from alphavantage.co"
    )
    parser.add_argument(
        "--api-base-url", type=str, help="Exact base url of api to request data from alphavantage.co"
    )
    parser.add_argument(
        "--api-data-interval", type=str, help="Interval between stock states requested from alphavantage.co"
    )
    parser.add_argument(
        "--request-api-data", type=bool,
        help="Switcher between modes that enable to request"
             "data from alphavantage.co."
    )
    parser.add_argument(
        "--secondary-pages-scrapping", type=bool,
        help="Switcher between modes that enable not to scrap"
        "secondary pages of each article." ###Alex
    )
    parser.add_argument(
        "--debug_number-of-pages",
        type=int,
        help="Number of news main pages to scrap in debug mode",
    )
    parser.add_argument(
        "--deployment-number-of-pages",
        type=int,
        help="Number of news main pages to scrap in deployment mode",
    )
    parser.add_argument(
        "--debug-number-of-urls",
        type=int,
        help="Number of articles to save and show in debug mode"
             "(used only in debug mode)",
    )
    parser.add_argument(
        "-p",
        "--parallel",
        action="store_true",
        help="Run the scraping in parallel using grequests.",
    )

    print("initialise_parser() was ended")
    return parser


def config_logging(log_file_name: str) -> None:
    """
    Initializes logger instance based on provided log file name
    and sets log level to DEBUG.
    Log level setting may be updated later outside this function.

    :param log_file_name: str, the name of the log file to save the logs to
    :return: None
    """
    if log_file_name[-4:] != ".log":
        print("Log file creation error, the logfile is expected to end as .log")
        sys.exit()

    with open(log_file_name, "wb"):
        pass

    logging.basicConfig(
        filename=log_file_name,
        level=logging.DEBUG,
        format="%(levelname)s - %(asctime)s - %(message)s",
    )


def check_config_file(config_file_name: str, required_constants: list) -> dict:
    """
    Checks that config file exists and consists of required_constants.
    Stops the whole program in case of any issue.

    :param config_file_name: a name of config file to  open
    :param required_constants: a list of expected params names
    :return: obj: a dict of params received from the file
    """
    logging.info("check_config_file() started")
    try:
        with open(config_file_name, "rb") as my_file:
            obj = my_file.read()
            obj = json.loads(obj)

        if set(required_constants).intersection(list(obj.keys())) == set(
                required_constants
        ):
            logging.info(
                "all config parameters loaded successfully from config file")
        else:
            logging.error(
                "Config file does not contain the one or more required parameters"
            )
            logging.critical("Exiting program...")
            sys.exit()

        logging.info(
            "Config file loaded successfully, check_config_file() completed")
        return obj
    except FileNotFoundError:
        logging.error("Config file not found")
        logging.critical("Exiting program...")
        sys.exit()


def load_config(config_file_name: str) -> dict:
    """
    Loads the configuration file settings config_file_name.

    :param config_file_name: str, the name of config file to read
    :return: the list of parameters received from the config file
    """
    logging.info("load_config() started, config_file_name : %s",
                 config_file_name)

    obj = check_config_file(config_file_name, REQUIRED_CONSTANTS)

    configs = {}
    for key in obj.keys():
        config_var_name = key.lower()
        if 'comment' not in config_var_name:
            configs[config_var_name] = obj[key]

    configs['site_url'] = "/".join(obj["URL"].split("/")[0:-1])

    logging.info("load_config() completed")

    return configs


def set_config() -> dict:
    """
    Gets global variables values from config file,
    updates them with values from command line arguments
    and then returns the list of global variables values.

    :return: the list of global variables values
    """
    logging.info("set_config() started")

    args_configs = vars(ARGS)

    configs = load_config(ARGS.config_file)

    # update with the CLI ones
    for key, _ in configs.items():
        if args_configs.get(key):
            logging.info(
                "Setting command line argument %s as %s",
                key,
                args_configs[key],
            )
            configs[key] = args_configs[key]
            if key == 'url':
                configs['site_url'] = "/".join(args_configs[key].split("/")[0:-1])
        logging.info("%s + is: %s", key, configs[key])  # Alex

    if configs['debug_mode']:
        # debug mode number of pages
        configs['number_of_pages'] = configs['debug_number_of_pages']
    else:
        configs['number_of_pages'] = configs['deployment_number_of_pages']

    logging.info("number of pages is: %s", configs['number_of_pages'])
    logging.info("set_config() completed")

    return configs


ARGS = initialise_parser().parse_args()
config_logging(ARGS.log_file)
glob = set_config()
DEBUG_MODE = glob['debug_mode']
DEBUG_LOG_LEVEL = glob['debug_log_level']
DEPLOYMENT_LOG_LEVEL = glob['deployment_log_level']
URL = glob['url']
SITE_URL = glob['site_url']
DEBUG_NUMBER_OF_URLS = glob['debug_number_of_urls']
NUMBER_OF_PAGES = glob['number_of_pages']
PARALLEL = glob['parallel']
CHROME_DRIVER_PATH = glob['chrome_driver_path']
MYSQL_CONFIG_FILE = glob['mysql_config_file']
SECONDARY_PAGES_SCRAPPING = glob['secondary_pages_scrapping']
REQUEST_API_DATA = glob['request_api_data']
API_KEY = glob['api_key']
API_BASE_URL = glob['api_base_url']
API_DATA_INTERVAL = glob['api_data_interval']
del glob


def load_config_file_database() -> tuple[str, str, list]:
    """
    Gets the full path to the configuration file .json
    and load it into the configuration.

    :return: a tuple of parameters of database setting:
            username, password, main commands (including database name)
    """
    try:
        with open(MYSQL_CONFIG_FILE, "rb") as my_file:
            obj = my_file.read()
            obj = json.loads(obj)
        print("Config file loaded successfully")
    except FileNotFoundError:
        print("Config file not found")
        print("Exiting program...")
        sys.exit()

    username_ = obj["USER_NAME"]
    password_ = obj["PASSWORD"]
    del obj["USER_NAME"]
    del obj["PASSWORD"]

    return username_, password_, obj


USER_NAME, PASSWORD, OTHER_SQL_CONFIG = load_config_file_database()


def set_log_level() -> None:
    """
    Change the logging level according to the DEBUG_MODE variable.

    :return: None
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
        logging.info("logging level set to: %s",
                     error_map.get(DEBUG_LOG_LEVEL))
    else:
        level_ = DEPLOYMENT_LOG_LEVEL
        logging.info("logging level set to: %s",
                     error_map.get(DEPLOYMENT_LOG_LEVEL))

    logger = logging.getLogger()
    logger.setLevel(level_)

    logging.info("load_logs() completed")


def url_request(url: str) -> str:
    """
    Requests the HTML page from the given string - URL,
    and returns the HTML page in str format.
    Adds small waiting time to avoid blocking.

    :param url: str, the url to get the HTML data from
    :return: str, the HTML page in str format
    """
    logging.info("url_request() was called with:\n %s", url)

    time.sleep(0.2)

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
        logging.error("Request failed with status code: %s",
                      response.status_code)
        print("closing program")
        logging.error("closing program")
        sys.exit()
    else:
        logging.info("Request fetched successfully, code=200")
        logging.info("url_request() was ended")
        return response.text


def url_to_soup(url: str) -> BeautifulSoup:
    """
    The function is deprecated due to site
    update with a lot of javascript.
    Use selenium_url_to_soup() instead.

    Requests the HTML page from the given string - URL,
    parse it with BeautifulSoup
    and returns the corresponding object.

    :param url: str, url to get the data from
    :return: BeautifulSoup, the data from the url
    """
    logging.info("url_to_soup() was called with:\n %s", url)

    html = url_request(url)

    soup = BeautifulSoup(html, "html.parser")

    logging.info("url_to_soup() ended")

    return soup


def selenium_url_to_soup(url: str) -> BeautifulSoup:
    """
    Requests the HTML page from the given string - URL,
    parse it with BeautifulSoup
    and returns the corresponding object.

    :param url: str, url to get the data from
    :return: BeautifulSoup, the data from the url
    """
    logging.info("selenium_url_to_soup() was called with:\n %s", url)

    html_content = get_html_content_with_driver(url)

    soup = BeautifulSoup(html_content, "html.parser")

    logging.info("selenium_url_to_soup() ended")

    return soup


def selenium_service_and_options() -> tuple:
    """
    Initializes and return service and options objects
    for selenium webdriver input.

    :return: service and options objects
    """
    logging.info("selenium_service_and_options() was called")

    service = Service(executable_path=CHROME_DRIVER_PATH)
    options = Options()

    options.add_argument("--log-level=3")

    # Add argument to hide browser window and make the process faster
    options.add_argument("--headless")

    # Some options to come over block against headless browsers
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/58.0.3029.110 Safari/537.3')
    options.add_argument('--disable-gpu')

    logging.info("selenium_service_and_options() ended")

    return service, options


def get_html_content_with_driver(url: str) -> str:
    """
    Uses selenium driver to get html_content of the provided page.

    :param url: the address to request
    :return: a string with html content of the page
    """
    logging.info("get_html_content_with_driver was called with\n %s", url)

    service, options = selenium_service_and_options()
    driver = webdriver.Chrome(service=service, options=options)

    # command to wait inside the headless browser window
    driver.implicitly_wait(3)

    driver.get(url)

    # Give some time for JavaScript to load the content.
    # Both driver.implicitly_wait and time.sleep are important in headless mode.
    for _ in tqdm(range(100)):
        time.sleep(0.03)

    html_content = driver.page_source
    driver.quit()

    return html_content


def check_percentage(percentage_string: str) -> str:
    """
    Checks for percentage string formatting.

    :param percentage_string: the string to test
    :return: "absent" or the string if in percent formatting
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
    return "0.0"


def add_data_links_and_titles(data: Tag) -> dict:
    """
    Extracts more price_change, price_change_time and ticker from the given select object.

    :param data: BeautifulSoup select output object to scan and extract data from
    :return: a list with mode data [price_change, price_change_time, ticker]
    """
    logging.info("add_data_links_and_titles() was called")

    try:
        ticker = data.footer.a.span.string
    except AttributeError:
        ticker = "None"
    output_dict = {'ticker': ticker}
    logging.info("extracted ticker:%s", ticker)

    try:
        price_change = data.footer.a.span.find_next_sibling().string
    except AttributeError:
        price_change = "None"

    price_change = check_percentage(price_change)
    output_dict['price_change'] = price_change
    logging.info("extracted price change: %s", price_change)

    now = datetime.now()
    price_change_time = (
        f"{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}"
    )
    output_dict['price_change_time'] = price_change_time
    logging.info("extracted price change time :%s", price_change_time)

    logging.info("extract_links_and_titles() was ended")

    return output_dict


def extract_links_and_titles(num_pages: int) -> dict:
    """
    Extracts article's links (full and short) from news main page(s).
    Outputs a dict of {title1: [href, title_id..],...}.

    :param num_pages: number of pages to scrap
    :return: a dict with data per title
    """
    logging.info("extract_links_and_titles() was called with:\n %s", num_pages)

    output_dict = {}

    for i in range(1, num_pages + 1):
        url = URL + str(i)

        link_soup = selenium_url_to_soup(url)

        select_object = link_soup.select("article div div")

        for data in select_object:
            title_data = {}
            title = data.h3.a.text
            href = data.h3.a.attrs.get("href")
            href = SITE_URL + href[: href.find("?")]
            title_data['href'] = href
            title_id = re.search(r"\d+", href).group()
            title_data['title_id'] = title_id
            output_dict[title] = title_data
            logging.info("extracted title: %s with data: %s",
                         title, title_data)

            title_data2 = add_data_links_and_titles(data)
            output_dict[title].update(title_data2)
            logging.info("extracted ticker with data: %s ", title_data2)

    logging.info("extract_links_and_titles() was ended")
    return output_dict


def extract_data_from_soup(soup: BeautifulSoup) -> dict:
    """
    Extracts date, time and author from the soup of article page
    and returns them the list in the following format:
    [date_str, time, author].

    :param soup: the soup of article page
    :return: dict containing author, date_str and time
    """

    text = soup.text

    logging.info("extract_data_from_soup() was called for %s", text[:100])

    output_dict = {}

    match = re.search(r"By:\s+(\w+\s*)+", text)
    if match:
        author = match.group(0).replace("By: ", "").strip()
        logging.info("author added ! %s", author)
    else:
        author = None
        logging.info("author not found !! %s", author)
    output_dict['author'] = author
    logging.debug("extracted author %s", author)

    match = re.search(r"\w{3}\. \d{1,2}, \d{4}", text)
    if match:
        date_str = match.group()
        logging.info("date_str added ! %s", date_str)
    else:
        date_str = None
        logging.info("date_str not found !! %s", date_str)
    output_dict['date_str'] = date_str
    logging.debug("extracted publishing date_str %s", date_str)

    match = re.search(r"\d{1,2}:\d{2} [AP]M", text)
    if match:
        time_ = match.group()
        logging.info("time_ added ! %s", time_)
    else:
        time_ = None
        logging.info("time_ not found !! %s", time_)
    output_dict['time'] = time_
    logging.debug("extracted publishing time %s", time_)

    logging.info("extract_data_from_soup() was ended")
    return output_dict


def extract_data_from_articles(articles: dict) -> None:
    """
    Extracts data about articles
    and fills it into the provided dict,
    using the sequential approach.

    :param articles: dict of {title: link} of group of articles.
                    The values are subjects of change!
    :return: None
    """
    logging.info(
        "extract_data_from_articles() was called for # of articles %s", len(articles)
    )

    stop = DEBUG_NUMBER_OF_URLS if DEBUG_MODE else len(articles)

    for title, values in tqdm(list(articles.items())[:stop]):
        extracted_data = extract_data_from_soup(
            selenium_url_to_soup(values['href'])
        )
        articles[title].update(extracted_data)
        logging.debug("The extracted data was added to dataset.")

    logging.info("extract_data_from_articles() was ended")


def print_dict(dict_: dict) -> None:
    """
    A function that prints the dictionary.
    Using the DEBUG_NUMBER_OF_URLS variable
    as the number of articles to be printed.
    If debug mode in True.

    :param dict_:  dict with data about articles
    :return: None
    """
    stop = DEBUG_NUMBER_OF_URLS if DEBUG_MODE else len(dict_)

    spacer = "+----+---------------+--------------+---------------------+------------+"

    for i, (key, article_data) in enumerate(list(dict_.items())[:stop]):
        print(f"{spacer} \n {i} :")
        print(f"{key}")
        for data_key, item in article_data.items():
            print(f"{data_key}: {item}")
        print(spacer)


def time_some_function(function_: callable, args_list: list) -> tuple[str, any]:
    """
    Given the function name and the list of arguments,
    will execute the function and return the result and return
    in string format the time it took to execute the function.
    in the following format: 0:00:37.183115 = Hours:Minutes:Seconds.milliseconds

    :param function_: the function to measure the execution time of
    :param args_list: args of the function to measure the execution time of
    :return: the tuple of two elements: execution time and function output
    """
    logging.info("time_some_function() was called for %s", function_)

    start_time = time.time()
    result = function_(*args_list)
    end_time = time.time()
    time_taken = end_time - start_time
    logging.info("time_some_function() ended")
    return str(timedelta(seconds=time_taken)), result


def print_timing_function_results(time_lapse: str) -> None:
    """
    A function that prints the timing results and also logs the timing.

    :param time_lapse: string in the following format: 0:00:37.1831
    :return: None
    """
    logging.info("print_timing_function_results() started for %s", time_lapse)

    print("* * * * * * * * * * * * * * * * * * * * *")
    print(
        time_lapse,
        "= Hours:Minutes:Seconds.milliseconds to complete",
    )
    print("* * * * * * * * * * * * * * * * * * * * *")

    logging.info("print_timing_function_results() was ended")


def parallel_approach(my_dict: dict) -> None:
    """
    The function is temporarily out of order due to web-site issues.

    A function that scrapes data from secondary href sites using parallel approach.

    :param my_dict: dict of {title: link} items to fill with new data.
                    The values are the subjects of change!
    :return: None
    """
    logging.info("parallel_approach() started ")

    stop = DEBUG_NUMBER_OF_URLS if DEBUG_MODE else len(my_dict)

    # Create a list of requests
    requests_list = []
    urls = []

    for value in list(my_dict.values())[:stop]:
        urls.append(value[0])

    for url in urls:
        try:
            request = grequests.get(url)
            requests_list.append(request)
            logging.info("%s fetched successfully", url)
        except FileNotFoundError:
            logging.error("%s unreachable", url)
            logging.critical("Exiting program...")
            sys.exit()

    # Send requests in batches of 5
    responses = grequests.imap(requests_list, size=5)

    responses_dict = {
        response.url: extract_data_from_soup(
            BeautifulSoup(response.text, "html.parser")
        )
        for response in responses
    }

    for key, value in list(my_dict.items())[:stop]:
        my_dict[key] = my_dict.get(key, []) + responses_dict.get(value[0], [])

    logging.info("parallel_approach() was ended")


def get_intraday_stock_data(symbol, api_key=API_KEY, interval="5min") -> tuple[str, dict]:
    """
    Given stock symbol, api_key and interval requests from alphavantage.co
    historical data of the stock: open, close, high, low and volume of sales in each interval.

    :param symbol: stock symbol to get data about
    :param api_key: api_key to request data with
    :param interval: an interval between requested states

    :return: tuple containing symbol and requested data
    """
    function = "TIME_SERIES_INTRADAY"
    output_size = "compact"  # use "full" for more historical data

    url = f"{API_BASE_URL}function={function}&symbol={symbol}&interval={interval}" \
          f"&outputsize={output_size}&apikey={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        time_series = data.get(f"Time Series ({interval})")
        return symbol, time_series
    else:
        print("Error fetching data:", response.status_code)
        logging.error("Error fetching data:", response.status_code)
        sys.exit()


def prices_to_db(ticker, dict_api):
    """
    given the prices dictionary and the ticker name
    update the database accordingly
    """
    logging.info("prices_to_db(() called for ticker: %s ", ticker)

    command = f"SELECT id FROM stock WHERE ticker_symbol = '{ticker}'"
    ticker_id = database_query(command)[0][0]

    for key, values in dict_api.items():
        command = "INSERT INTO prices "
        command += "(ticker_symbol_id, datetime, open, high, low, close, volume) "
        command += f"VALUES ('{ticker_id}', '{key}', {values['1. open']}, "
        command += f"{values['2. high']}, {values['3. low']}, {values['4. close']}, "
        command += f"{values['5. volume']})"

        database_query(command, commit_=True)

    logging.info("new_article() ended")


def tickers_to_db(tickers: list):
    """
    This function organises saving of  API data for several symbols to 'prices' table.

    :param tickers: list of symbols(strings) like ['AAPL', 'NVDA']

    :return: None
    """
    for ticker in tickers:
        prices_to_db(
            *get_intraday_stock_data(
                symbol = ticker,
                api_key=API_KEY,
                interval=API_DATA_INTERVAL
            )
        )


def database_query(
        query_: str,
        commit_: bool = False,
        print_result_: bool = False,
        data_base_: str = "market",
) -> list:
    """
    Wrapper of SQL query executor. Can print the output,
    provide ability to set database name
    and even not to commit the query to database at all.

    :param query_: str, SQL query to be executed
    :param commit_: bool = False, whether to commit the changes to database by the query
    :param print_result_: bool = False: whether to print the result of the query
    :param data_base_: str, database name
    :return: the output of .fetchall() function, or None
    """
    logging.info(
        "database_query() called with: %s , commit: %s, print %s:",
        query_,
        commit_,
        print_result_,
    )

    if "DATABASE" in query_:
        data_base_ = ""

    try:
        # Establish a connection to the MySQL database
        my_db = mysql.connector.connect(
            host="localhost", user=USER_NAME, password=PASSWORD, database=data_base_
        )

        # Create a cursor object to execute SQL queries
        my_cursor = my_db.cursor()

        # Execute the SQL query to show all databases
        my_cursor.execute(query_)

        # Fetch all rows from the result set
        result = my_cursor.fetchall()

        # Create a PrettyTable object and add the column header dynamically
        table = PrettyTable()

        logging.info("Query executed successfully")

        if print_result_:
            try:
                table.field_names = [i[0] for i in my_cursor.description]
            except IndexError:
                print(f"\nGOT exception for an index error: {IndexError}")
            except TypeError:
                print(f"\nGOT exception for a type error: {TypeError}")

        # Add each row to the table
        for row in result:
            table.add_row(
                [col.decode("utf-8") if isinstance(col, bytes)
                 else col for col in row]
            )

        # Display the table
        if print_result_:
            print(table)

        # Commit the changes to the database
        if commit_:
            my_db.commit()

        # Close the cursor and database connection
        if my_cursor:
            my_cursor.close()
        if my_db:
            my_db.close()

    except mysql.connector.Error as error:
        print(f"Error executing query: {error}")
        result = None

    logging.info("database_query() ended with result: %s", result)
    return result


def new_article(title: str, article_data: dict) -> None:
    """
    Executes a query of adding new item to articles table of database.

    Note :
     values = 0link, 1article_id, 2price_change, 3price_change_time,
     4ticker_symbol, 5article_timestamp, 6author_name

    :param title: str, the title of the article
    :param article_data: dict, the data to be filled
    :return: None
    """
    logging.info("new_article() called for title: %s ", title)

    # add new "name" in the table "author" if not already present
    author_query = (
        f"INSERT INTO author (name) SELECT '{article_data['author']}' WHERE NOT "
        + f"EXISTS(SELECT name FROM author WHERE name = '{article_data['author']}');"
    )
    database_query(author_query, commit_=True)

    # add the data only if there are no articles in the article table with the same title
    article_query = (
        "INSERT INTO article (title, link, datetime_posted, author_id) "
        + f"SELECT '{title}', '{article_data['href']}', '{article_data['date_str']}', "
        + f"(SELECT id FROM author WHERE name = '{article_data['author']}')"
        + f"WHERE NOT EXISTS (SELECT id FROM article WHERE title = '{title}');"
    )
    database_query(article_query, commit_=True)

    # update the stock table with the data
    stock_query = (
        "INSERT INTO stock(ticker_symbol, price_change, datetime_change, article_id) "
        + f"VALUES('{article_data['ticker']}', '{article_data['price_change']}', "
        + f"'{article_data['price_change_time']}', "
        + f"(SELECT id FROM article WHERE title = '{title}'));"
    )
    database_query(stock_query, commit_=True)

    logging.info("new_article() ended")


def dict_to_db(data: dict) -> None:
    """
    Updates the database with all the entries from the dict provided.

    :param data: dict, the data to save to db
    :return: None
    """
    logging.info("dict_to_db() called for len(data): %s ", len(data))

    stop = DEBUG_NUMBER_OF_URLS if DEBUG_MODE else len(data)

    for title, article_data in list(data.items())[:stop]:
        # Re-format title to MySQL VARCHAR format
        title = title.translate(str.maketrans("", "", string.punctuation))

        # Re-format price_change to MySQL-DATETIME format
        article_data['price_change'] = article_data['price_change'].strip("%")

        # Re-format article_timestamp to MySQL-DATETIME format
        date_obj = datetime.strptime(article_data['date_str'], "%b. %d, %Y")
        time_obj = datetime.strptime(article_data['time'], "%I:%M %p")
        article_data['date_str'] = datetime.combine(
            date_obj.date(), time_obj.time())

        # Update the date from Eastern Time (ET) to Jerusalem Time Zone (GMT+2)
        eastern = pytz.timezone("US/Eastern")
        jerusalem = pytz.timezone("Asia/Jerusalem")
        dt_eastern = eastern.localize(article_data['date_str'])
        article_data['date_str'] = dt_eastern.astimezone(jerusalem)

        new_article(title, article_data)

        logging.info("dict_to_db() ended successfully")


def initialize_db() -> None:
    """
    Drops the database "market" tables and,
    initialize it back with the empty tables.

    :return: None
    """
    logging.info("initialize_db() was called")

    for item in OTHER_SQL_CONFIG:
        database_query(OTHER_SQL_CONFIG[item], commit_=True)

    logging.info("initialize_db() was ended successfully")


def nice_print_article() -> None:
    """
    Prints the article table in the database in a pretty format.

    :return: None
    """
    data = database_query("SELECT * FROM article")

    separator = (
        "+----+---------------+--------------+---------------------+------------+"
    )

    # Print the first separator
    print(separator)

    for row in data:
        print(
            f"id: {row[0]} | publish_time: {row[3]} | author_id: {row[4]} | title:|>")
        print(f"{row[1]}")
        print(f"link: {row[2]}")
        print(separator)


def main() -> None:
    """
    The main function.

    :return: None
    """
    logging.info("main() started")

    logging.debug("DEBUG before set_log_level()")
    set_log_level()
    logging.debug("DEBUG after set_log_level()")

    print("debug mode is:", DEBUG_MODE)
    print("number of pages to scrape is:", NUMBER_OF_PAGES)

    time_str1, my_dict = time_some_function(
        extract_links_and_titles, [NUMBER_OF_PAGES])
    print(f"scraping the main {NUMBER_OF_PAGES} web pages took: ")
    print_timing_function_results(time_str1)

    print_dict(my_dict)

    if SECONDARY_PAGES_SCRAPPING:
        if not PARALLEL:
            time_str2, _ = time_some_function(
                extract_data_from_articles, [my_dict])
        else:
            print("\n=============="
                  "Sorry, parallel mode is temporarily out of order!"
                  "==============\n")
            # time_str2, _ = time_some_function(parallel_approach, [my_dict])
            time_str2, _ = time_some_function(
                extract_data_from_articles, [my_dict])

        print("scraping the secondary webpages took: ")
        print_timing_function_results(time_str2)

        print_dict(my_dict)

    else:
        # Get the current date and time in New York
        time_zone = pytz.timezone('America/New_York')
        now = datetime.now(time_zone)
        date_str = now.strftime("%b. %d, %Y")
        time_str = now.strftime("%I:%M %p")
        for key in my_dict.keys():
            my_dict[key].update({
                'author': 'None',
                'date_str': date_str,
                'time': time_str
            })

    initialize_db()

    dict_to_db(my_dict)

    tickers = database_query("SELECT DISTINCT ticker_symbol FROM stock")[:-1]
    tickers = [x[0] for x in tickers]

    tickers_to_db(tickers)

    nice_print_article()
    database_query("SELECT * FROM stock", print_result_=True)
    database_query("SELECT * FROM author", print_result_=True)
    database_query("SELECT * FROM prices ORDER BY datetime LIMIT 5", print_result_=True)

    logging.info("main() completed")


if __name__ == "__main__":
    main()
