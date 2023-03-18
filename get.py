"""
debug
"""
import sys
import logging
import re
import requests
from bs4 import BeautifulSoup

with open("debug.log", "wb"):  # clear the log file
    pass
logging.basicConfig(
    filename="debug.log", level=10, format="%(levelname)s - %(message)s"
)


#url = """https://seekingalpha.com/news/3948677-pfizer-developing-new-nurtec-odt-migraine-packaging-recall-bloomberg"""
#url = """https://seekingalpha.com/news/3948648-losses-from-equity-reits-narrow-as-major-indices-rebound-from-banking-crisis-impact"""
url = """https://seekingalpha.com/news/3948552-tiktoks-moment-of-truth-coming-fallout-could-spread-far-and-wide"""

url = """https://seekingalpha.com/market-news?page="""

try:
    soup = BeautifulSoup(requests.get(url, timeout=10).text, "html.parser")
    logging.info("fetched successfully")
except FileNotFoundError:
    logging.error("unreachable !")
    logging.critical("Exiting program...")
    sys.exit()

logging.debug(soup.prettify())

text = soup.text

match = re.search(r"\w{3}\. \d{1,2}, \d{4}", text)
if match:
    price_change = match.group()
    logging.info("price_change added ! %s", price_change)
else:
    price_change = None
    logging.info("price_change not found !! %s", price_change)

match = re.search(r"\d{1,2}:\d{2} [AP]M", text)
if match:
    time_ = match.group()
    logging.info("time_ added ! %s", time_)
else:
    time_ = None
    logging.info("time_ not found !! %s", time_)


ans = [time_, price_change]
print(ans)
