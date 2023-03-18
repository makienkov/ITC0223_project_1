"""
debug
"""
import sys
import logging
import re
import requests
from bs4 import BeautifulSoup
import datetime


with open("debug.log", "wb"):  # clear the log file
    pass
logging.basicConfig(
    filename="debug.log", level=10, format="%(levelname)s - %(message)s"
)

URL = """https://seekingalpha.com/market-news?page="""


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


output_dict = {}

num_pages = 1

for i in range(1, num_pages + 1):
    url_ = URL + str(i)

    link_soup = url_to_soup(url_)
    
    def split(input_string):
        pattern = r'^(\w+)\s+(-?\d+\.\d+%)\s+(.*)$'
        match = re.match(pattern, input_string)
        if match:
            return [match.group(1), match.group(2), match.group(3)]
        else:
            raise ValueError("Invalid input string")
    
    select_object = link_soup.select("article div div footer")

    for data in select_object:
        title_data = []
        clean_text = re.sub(r'\s*\d+\s*Comments?', '', data.text)

        ticker = clean_text.split()[0]
        clean_text  = clean_text.split()[1:]
        price_change = str(clean_text[0].split("%")[0]) +"%"
        title_data.append(price_change)
        now = datetime.datetime.now()
        price_change_time = "{}/{}/{} {}:{}:{}".format(now.year, now.month, now.day, now.hour, now.minute, now.second)
        title_data.append(price_change_time)
        clean_text[0] = "".join(clean_text[0].split("%")[1:])
        date_article = " ".join(clean_text)
        title_data.append(price_change)
        logging.info("extracted title: %s with data: %s", "title", title_data)

        
    

        
        




# text = soup.text

# match = re.search(r"\w{3}\. \d{1,2}, \d{4}", text)
# if match:
#     price_change = match.group()
#     logging.info("price_change added ! %s", price_change)
# else:
#     price_change = None
#     logging.info("price_change not found !! %s", price_change)

# match = re.search(r"\d{1,2}:\d{2} [AP]M", text)
# if match:
#     time_ = match.group()
#     logging.info("time_ added ! %s", time_)
# else:
#     time_ = None
#     logging.info("time_ not found !! %s", time_)


# ans = [time_, price_change]
# print(ans)
