"""
!/usr/bin/env python3
coding=utf-8
----------------------------------------------------------------
Global scope
----------------------------------------------------------------
"""
import time
import sys
import logging
import json
import re
from datetime import datetime
from datetime import timedelta
import grequests
import requests
from bs4 import BeautifulSoup
import pytz
import mysql.connector
from prettytable import PrettyTable

CONFIG_FILE_NAME = "conf.json"

LOG_FILE_NAME = ".".join(__file__.split(".")[:-1]) + ".log"

with open(LOG_FILE_NAME, "wb"):
    pass

logging.basicConfig(
    filename=LOG_FILE_NAME,
    level=logging.DEBUG,
    format="%(levelname)s - %(asctime)s - %(message)s",
)


def load_config():
    """
    Loads the configuration file settings CONFIG_FILE_NAME.
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
        "PARALLEL",
    ]

    try:
        with open(CONFIG_FILE_NAME, "rb") as my_file:
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
    parallel_ = obj["PARALLEL"]

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
    logging.info("parallel enabled ? : %s", parallel_)

    logging.info("load_config() completed")

    return [
        debug_mode_,
        debug_log_level_,
        deployment_log_level_,
        url_,
        site_url_,
        debug_number_of_urls_,
        number_of_pages,
        parallel_,
    ]


glob = load_config()
DEBUG_MODE = glob[0]
DEBUG_LOG_LEVEL = glob[1]
DEPLOYMENT_LOG_LEVEL = glob[2]
URL = glob[3]
SITE_URL = glob[4]
DEBUG_NUMBER_OF_URLS = glob[5]
NUMBER_OF_PAGES = glob[6]
PARALLEL = glob[7]
del glob

PATH_TO_CONFIGURATION_FILE = "mysql_connector.json"


def load_config_file_database():
    """
    get the full path to the configuration file .json
    and load it into the configuration
    """
    try:
        with open(PATH_TO_CONFIGURATION_FILE, "rb") as my_file:
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
    return "0.0"


def add_data_links_and_titles(data2: str) -> list[str]:
    """A function that:
    extracts more data from the given select object,
    :param data2: soup  select object
    :return: a list with mode data [price_change, price_change_time]
    """
    logging.info("add_data_links_and_titles() was called")

    clean_text = re.sub(r"\s*\d+\s*Comments?", "", data2)
    clean_text = clean_text.split()[1:]
    try:
        price_change = str(clean_text[0].split("%")[0]) + "%"
    except Exception as e:
        logging.info("Error occurred while extracting percentage:%s", e)
        price_change = "0.0"

    price_change = check_percentage(price_change)
    logging.info("extracted price change: %s", price_change)

    now = datetime.now()
    price_change_time = (
        f"{now.year}/{now.month}/{now.day} {now.hour}:{now.minute}:{now.second}"
    )

    logging.info("extracted price change:%s", price_change_time)

    logging.info("extract_links_and_titles() was ended")

    return [price_change, price_change_time]


def extract_links_and_titles(num_pages):
    """A function that:
    extracts article's links (full and short) from news main page(s).
    Outputs a dict of {title1: [href, title_id..],...}

    :param num_pages: number of pages to scrap
    :return: a dict with data per title
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

            title_data2 = add_data_links_and_titles(data2.text)
            output_dict[title] += title_data2

    logging.info("extract_links_and_titles() was ended")
    return output_dict


def extract_data_from_soup(soup):
    """A function that:
    extracts data from soup of article page
    and returns the dictionary of single item in the following format:
    title: [ticker, date_str, time, author]
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


def extract_data_from_articles(articles: dict):
    """
    Extracts data about articles
    and fills it into the provided dict,
    using the sequential approach
    """
    logging.info(
        "extract_data_from_articles() was called for # of articles %s", len(articles)
    )

    stop = DEBUG_NUMBER_OF_URLS if DEBUG_MODE else len(articles)

    for title, values in list(articles.items())[:stop]:
        articles[title] += extract_data_from_soup(url_to_soup(values[0]))

    logging.info("extract_data_from_articles() was ended")


def print_dict(dict_):
    """
    A function that prints the dictionary.
    Using the DEBUG_NUMBER_OF_URLS variable
    as the number of articles to be printed.
    If debug mode in True.
    """
    stop = DEBUG_NUMBER_OF_URLS if DEBUG_MODE else len(dict_)

    for i, (key, value) in enumerate(list(dict_.items())[:stop]):
        print(f"{i} :**************************")
        print(f"{key}")
        for item in value:
            print(item)
        print("*****************************")


def time_some_function(function_, args_list: list) -> tuple[str, any]:
    """A function that:
    given the function name and the list of arguments,
    will execute the function and return the result and return
    in string format the time it took to execute the function.
    in the following format: 0:00:37.183115 = Hours:Minutes:Seconds.milliseconds
    """
    logging.info("time_some_function() was called for %s", function_)

    start_time = time.time()
    result = function_(*args_list)
    end_time = time.time()
    time_taken = end_time - start_time
    logging.info("time_some_function() ended")
    return str(timedelta(seconds=time_taken)), result


def print_timing_function_results(time_lapse: str):
    """
    A function that prints the timing results.
    and also logs the timing.
    time_lapse is a string in the following format: 0:00:37.1831
    """
    logging.info("print_timing_function_results() started for %s", time_lapse)

    print("* * * * * * * * * * * * * * * * * * * * *")
    print(
        time_lapse,
        "= Hours:Minutes:Seconds.milliseconds to complete",
    )
    print("* * * * * * * * * * * * * * * * * * * * *")

    logging.info("print_timing_function_results() was ended")


def parallel_approach(my_dict: dict):
    """
    A function that scrapes data from secondary href sites using parallel approach
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
        my_dict[key] += responses_dict[value[0]]

    logging.info("parallel_approach() was ended")


def database_query(query_, commit_=False, print_result_=False, data_base_="market"):
    """
    data_base: database name
    query: SQL query to be executed
    commit=False: whether to commit the changes to database by the query
    print_result=False: whether to print the result of the query
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
                [col.decode("utf-8") if isinstance(col, bytes) else col for col in row]
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


def new_article(title, values):
    """
    a case when the article is new,
    update the database accordingly
    note :
     values = 0link, 1article_id, 2price_change, 3price_change_time,
     4ticker_symbol, 5article_timestamp, 6author_name
    """
    logging.info("new_article() called for title: %s ", title)

    # add new "name" in the table "author" if not already present
    author_query = (
            f"INSERT INTO author (name) SELECT '{values[6]}' WHERE NOT "
            + f"EXISTS(SELECT name FROM author WHERE name = '{values[6]}');"
    )
    database_query(author_query, commit_=True)

    # add the data only if there are no articles in the article table with the same title
    article_query = \
        "INSERT INTO article (title, link, datetime_posted, author_id) "\
        + f"SELECT '{title}', '{values[0]}', '{values[5]}', "\
        + f"(SELECT id FROM author WHERE name = '{values[6]}')"\
        + f"WHERE NOT EXISTS (SELECT id FROM article WHERE title = '{title}');"
    database_query(article_query, commit_=True)

    # update the stock table with the data
    stock_query = \
        "INSERT INTO stock(ticker_symbol, price_change, datetime_change, article_id) " \
        + f"VALUES('{values[4]}', '{values[2]}', '{values[3]}', " \
        + f"(SELECT id FROM article WHERE title = '{title}'));"
    database_query(stock_query, commit_=True)

    logging.info("new_article() ended")


def dict_to_db(data):
    """
    take the dictionary .
    update the database with all the entries.
    note:
      values =  0link, 1article_id, 2price_change, 3price_change_time,
                4ticker_symbol, 5date_str, 6time_str, 7author_name
    """
    logging.info("dict_to_db() called for len(data): %s ", len(data))

    stop = DEBUG_NUMBER_OF_URLS if DEBUG_MODE else len(data)

    # for value in list(my_dict.values())[:stop]:
    #     urls.append(value[0])

    for title, values in list(data.items())[:stop]:
        # Re-format title MySQL-string  format
        title = title.strip("'\"")

        # Re-format price_change to MySQL-DATETIME format
        values[2] = values[2].strip("%")

        # Re-format price_change_time to MySQL-DATETIME format
        values[3] = datetime.strptime(values[3], "%Y/%m/%d %H:%M:%S")

        # Re-format article_timestamp to MySQL-DATETIME format
        date_obj = datetime.strptime(values[5], "%b. %d, %Y")
        time_obj = datetime.strptime(values[6], "%I:%M %p")
        values[5] = datetime.combine(date_obj.date(), time_obj.time())

        # Update the date from Eastern Time (ET) to Jerusalem Time Zone (GMT+2)
        eastern = pytz.timezone("US/Eastern")
        jerusalem = pytz.timezone("Asia/Jerusalem")
        dt_eastern = eastern.localize(values[5])
        values[5] = dt_eastern.astimezone(jerusalem)
        del values[6]

        new_article(title, values)

        logging.info("dict_to_db() ended successfully")


def initialize_db():
    """
    drop the database "market" tables and,
    initialize the database with the empty tables
    """
    logging.info("initialize_db() was called")

    for item in OTHER_SQL_CONFIG:
        # print(obj[item])
        database_query(OTHER_SQL_CONFIG[item], commit_=True)

    logging.info("initialize_db() was ended successfully")


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

    time_str1, my_dict = time_some_function(extract_links_and_titles, [NUMBER_OF_PAGES])
    print(f"scraping the main {NUMBER_OF_PAGES} web pages took: ")
    print_timing_function_results(time_str1)

    print_dict(my_dict)

    if not PARALLEL:
        time_str2, _ = time_some_function(extract_data_from_articles, [my_dict])
    else:
        time_str2, _ = time_some_function(parallel_approach, [my_dict])

    print("scraping the secondary webpages took: ")
    print_timing_function_results(time_str2)

    print_dict(my_dict)

    initialize_db()

    dict_to_db(my_dict)

    database_query("SELECT * FROM author", print_result_=True)
    database_query("SELECT * FROM article", print_result_=True)
    database_query("SELECT * FROM stock", print_result_=True)

    logging.info("main() completed")


if __name__ == "__main__":
    main()
