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
from bs4 import BeautifulSoup
import pytz
import mysql.connector
from prettytable import PrettyTable

FILE_NAME = ".".join(__file__.split(".")[:-1])


def initialise_parser():
    """
    The function initializes and returns the parser of user input.

    :return: Initialized parser object
    """
    print("initialise_parser() started")
    parser = argparse.ArgumentParser(description='Scrap info from "seeking alpha" site')
    parser.add_argument(
        "-s",
        "--shortened-info",
        action="store_false",
        help="Don't scrap news pages and get data," " only from main page(s).",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        default="conf.json",
        help="Path to the .json config file to use",
    )
    parser.add_argument(
        "--new-config-file",
        type=str,
        help="Name of new config .json file to save."
        "\nIf provided, the program will save all"
        "\nused params to the new .json file.",
    )
    parser.add_argument(
        "-l", "--log-file", default=FILE_NAME + ".log", help="Name of log file"
    )

    parser.add_argument(
        "--debug-log-level",
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
        help="Number of news main pages to scrap in deployment mode",
    )
    parser.add_argument(
        "-p",
        "--parallel",
        action="store_true",
        help="Run the scraping in parallel using grequests.",
    )

    print("initialise_parser() was ended")
    return parser


def config_logging(log_file_name: str = FILE_NAME + ".log"):
    """
    Initializes logger instance based on provided log file name
    and sets log level to DEBUG.
    Log level setting may be updated later outside this function.
    """
    with open(log_file_name, "wb"):
        pass

    logging.basicConfig(
        filename=log_file_name,
        level=logging.DEBUG,
        format="%(levelname)s - %(asctime)s - %(message)s",
    )


def load_config(config_file_name: str = "conf.json"):
    """
    Loads the configuration file settings config_file_name.
    Returns the global parameters
    """
    logging.info("load_config() started, config_file_name : %s", config_file_name)

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
        with open(config_file_name, "rb") as my_file:
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

    logging.info("load_config() completed")

    return [
        debug_mode_,
        debug_log_level_,
        deployment_log_level_,
        url_,
        site_url_,
        debug_number_of_urls_,
        deployment_number_of_pages_,
        debug_number_of_pages_,
        parallel_,
    ]


def set_config():
    """
    Gets global variables values from config file,
    updates them with values from command line arguments
    and then returns the list of global variables values.
    """
    logging.info("set_config() started")
    if ARGS.url:
        site_url = "/".join(ARGS.url.split("/")[0:-1])
    else:
        site_url = ARGS.url

    args_configs = [
        ARGS.debug_mode,
        ARGS.debug_log_level,
        ARGS.deployment_log_level,
        ARGS.url,
        site_url,
        ARGS.debug_number_of_urls,
        ARGS.debug_number_of_pages,
        ARGS.deployment_number_of_pages,
        ARGS.parallel,
    ]

    configs_names = [
        "debug_mode",
        "debug_log_level",
        "deployment_log_level",
        "url",
        "site_url",
        "debug_number_of_urls",
        "debug_number_of_pages",
        "deployment_number_of_pages",
        "parallel",
    ]

    if all(args_configs):
        # user entered all the parameters from CLI
        logging.info(
            "User entered all the params from the CLI, config file is being ignored."
        )
        configs = args_configs
    else:
        # some params need to be taken from config file...
        configs = load_config(ARGS.config_file)

        # ...and then updated with the CLI ones
        for i, arg_config in enumerate(args_configs):
            if arg_config:
                logging.info(
                    "Setting command line argument %s as %s",
                    configs_names[i],
                    arg_config,
                )
                configs[i] = arg_config

    if configs[0]:
        # debug mode number of pages
        configs[7] = configs[7]
    else:
        configs[7] = configs[6]

    logging.info("debug mode is: %s", configs[0])
    logging.info("debug log level is: %s", configs[1])
    logging.info("deployment log level  is: %s", configs[2])
    logging.info("URL is: %s", configs[3])
    logging.info("site URL is: %s", configs[4])
    logging.info("debug number of urls_ is: %s", configs[5])
    logging.info("number of pages is: %s", configs[7])
    logging.info("parallel enabled ? : %s", configs[8])

    logging.info("set_config() completed")

    return configs


ARGS = initialise_parser().parse_args()
config_logging(ARGS.log_file)
glob = set_config()
SCRAP_INDIVIDUAL_PAGES = ARGS.shortened_info
DEBUG_MODE = glob[0]
DEBUG_LOG_LEVEL = glob[1]
DEPLOYMENT_LOG_LEVEL = glob[2]
URL = glob[3]
SITE_URL = glob[4]
DEBUG_NUMBER_OF_URLS = glob[5]
NUMBER_OF_PAGES = glob[7]
PARALLEL = glob[8]
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


def add_data_links_and_titles(data) -> list[str]:
    """A function that:
    extracts more data from the given select object,
    :param data: soup  select object
    :return: a list with mode data [price_change, price_change_time, ticker]
    """
    logging.info("add_data_links_and_titles() was called")

    try:
        ticker = data.footer.a.span.string
    except AttributeError:
        ticker = "None"

    try:
        price_change = data.footer.a.span.find_next_sibling().string
    except AttributeError:
        price_change = "None"

    price_change = check_percentage(price_change)
    logging.info("extracted price change: %s", price_change)

    now = datetime.now()
    price_change_time = (
        f"{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}"
    )

    logging.info("extracted price change time :%s", price_change_time)

    logging.info("extracted ticker:%s", ticker)

    logging.info("extract_links_and_titles() was ended")

    return [price_change, price_change_time, ticker]


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

        select_object = link_soup.select("article div div")

        for data in select_object:
            title_data = []
            title = data.h3.a.text
            href = data.h3.a.attrs.get("href")
            href = SITE_URL + href[: href.find("?")]
            title_data.append(href)
            title_id = re.search(r"\d+", href).group()
            title_data.append(title_id)
            output_dict[title] = title_data
            logging.info("extracted title: %s with data: %s", title, title_data)

            title_data2 = add_data_links_and_titles(data)
            output_dict[title] += title_data2
            print()

    logging.info("extract_links_and_titles() was ended")
    return output_dict


def extract_data_from_soup(soup):
    """A function that:
    extracts data from soup of article page
    and returns the dictionary of single item in the following format:
    title: [date_str, time, author]
    """

    text = soup.text

    logging.info("extract_data_from_soup() was called for %s", text[:100])

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
    return [date_str, time_, author]


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
        articles[title] = articles.get(title, []) + extract_data_from_soup(
            url_to_soup(values[0])
        )

    logging.info("extract_data_from_articles() was ended")


def print_dict(dict_):
    """
    A function that prints the dictionary.
    Using the DEBUG_NUMBER_OF_URLS variable
    as the number of articles to be printed.
    If debug mode in True.
    """
    stop = DEBUG_NUMBER_OF_URLS if DEBUG_MODE else len(dict_)

    separator = (
        "+----+---------------+--------------+---------------------+------------+"
    )

    for i, (key, value) in enumerate(list(dict_.items())[:stop]):
        print(f"{separator} \n {i} :")
        print(f"{key}")
        for item in value:
            print(item)
        print(separator)


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
        my_dict[key] = my_dict.get(key, []) + responses_dict.get(value[0], [])

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
    article_query = (
        "INSERT INTO article (title, link, datetime_posted, author_id) "
        + f"SELECT '{title}', '{values[0]}', '{values[5]}', "
        + f"(SELECT id FROM author WHERE name = '{values[6]}')"
        + f"WHERE NOT EXISTS (SELECT id FROM article WHERE title = '{title}');"
    )
    database_query(article_query, commit_=True)

    # update the stock table with the data
    stock_query = (
        "INSERT INTO stock(ticker_symbol, price_change, datetime_change, article_id) "
        + f"VALUES('{values[4]}', '{values[2]}', '{values[3]}', "
        + f"(SELECT id FROM article WHERE title = '{title}'));"
    )
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

    for title, values in list(data.items())[:stop]:
        # Re-format title to MySQL VARCHAR format
        title = title.translate(str.maketrans("", "", string.punctuation))

        # Re-format price_change to MySQL-DATETIME format
        values[2] = values[2].strip("%")

        # Re-format article_timestamp to MySQL-DATETIME format
        date_obj = datetime.strptime(values[5], "%b. %d, %Y")
        time_obj = datetime.strptime(values[6], "%I:%M %p")
        values[5] = datetime.combine(date_obj.date(), time_obj.time())

        # Update the date from Eastern Time (ET) to Jerusalem Time Zone (GMT+2)
        eastern = pytz.timezone("US/Eastern")
        jerusalem = pytz.timezone("Asia/Jerusalem")
        dt_eastern = eastern.localize(values[5])
        values[5] = dt_eastern.astimezone(jerusalem)
        values[6], values[7] = values[7], values[6]

        new_article(title, values)

        logging.info("dict_to_db() ended successfully")


def initialize_db():
    """
    drop the database "market" tables and,
    initialize the database with the empty tables
    """
    logging.info("initialize_db() was called")

    for item in OTHER_SQL_CONFIG:
        database_query(OTHER_SQL_CONFIG[item], commit_=True)

    logging.info("initialize_db() was ended successfully")


def nice_print_article():
    """
    print the article table in the database
    in a pretty format.
    """
    data = database_query("SELECT * FROM article")

    separator = (
        "+----+---------------+--------------+---------------------+------------+"
    )

    # Print the first separator
    print(separator)

    for row in data:
        print(f"id: {row[0]} | publish_time: {row[3]} | author_id: {row[4]} | title:|>")
        print(f"{row[1]}")
        print(f"link: {row[2]}")
        print(separator)


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

    if SCRAP_INDIVIDUAL_PAGES:
        if not PARALLEL:
            time_str2, _ = time_some_function(extract_data_from_articles, [my_dict])
        else:
            time_str2, _ = time_some_function(parallel_approach, [my_dict])

        print("scraping the secondary webpages took: ")
        print_timing_function_results(time_str2)

        print_dict(my_dict)

    initialize_db()

    dict_to_db(my_dict)

    nice_print_article()
    database_query("SELECT * FROM stock", print_result_=True)
    database_query("SELECT * FROM author", print_result_=True)

    logging.info("main() completed")


if __name__ == "__main__":
    main()
