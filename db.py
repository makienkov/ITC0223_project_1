"""
!/usr/bin/env python3
coding=utf-8
"""
import sys
import logging
import json
from datetime import datetime
import pytz
import mysql.connector
from prettytable import PrettyTable

LOG_FILE_NAME = ".".join(__file__.split(".")[:-1]) + ".log"

with open(LOG_FILE_NAME, "wb"):
    pass

logging.basicConfig(
    filename=LOG_FILE_NAME,
    level=logging.INFO,
    format="%(levelname)s - %(asctime)s - %(message)s",
)

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


def print_dict(dict_):
    """
    A function that prints the dictionary.
    Using the DEBUG_NUMBER_OF_URLS variable
    as the number of articles to be printed.
    If debug mode in True.
    """
    stop = len(dict_)

    for i, (key, value) in enumerate(list(dict_.items())[:stop]):
        print(f"{i} :**************************")
        print(f"{key}")
        for item in value:
            print(item)
        print("*****************************")


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
    article_query = "INSERT INTO article (title, link, datetime_posted, author_id) "
    article_query += f"SELECT '{title}', '{values[0]}', '{values[5]}', "
    article_query += f"(SELECT id FROM author WHERE name = '{values[6]}')"
    article_query += (
        f"WHERE NOT EXISTS (SELECT id FROM article WHERE title = '{title}');"
    )
    database_query(article_query, commit_=True)

    # update the stock table with the data
    stock_query = (
        "INSERT INTO stock(ticker_symbol, price_change, datetime_change, article_id) "
    )
    stock_query += f"VALUES('{values[4]}', '{values[2]}', '{values[3]}', "
    stock_query += f"(SELECT id FROM article WHERE title = '{title}'));"
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

    for title, values in data.items():
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
    my_dict = {
        "Rumors suggest that Maxim S. & Alexander M.were contacted by Warren Buffet": [
            "https://seekingalpha.com/news/3951282-israel-tech-challenge",
            3951282,
            -1.36,
            "2023/3/26 20:14:23",
            "FRC",
            "Mar. 26, 2023",
            "10:51 AM",
            "Israel Tech Challenge",
        ],
        "Maxim Shatzki and Alexander Makienkov form a Warren Buffetts fintech branch": [
            "https://seekingalpha.com/news/3951283-israel-tech-challenge2",
            3951283,
            +1.36,
            "2023/3/26 20:15:23",
            "AAA",
            "Mar. 26, 2023",
            "10:55 AM",
            "Israel Tech Challenge2",
        ],
    }

    print_dict(my_dict)

    initialize_db()

    dict_to_db(my_dict)

    database_query("SELECT * FROM author", print_result_=True)
    database_query("SELECT * FROM article", print_result_=True)
    database_query("SELECT * FROM stock", print_result_=True)


if __name__ == "__main__":
    main()
