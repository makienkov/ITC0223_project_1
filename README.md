# SeekingAlpha Web Scraping Project

![](https://assets.website-files.com/60623415e8fabe3c9c6f9280/6081fe0542a2037e6ecb4295_SA%20Logo%2020.4.21.png)

This is a Python project that web scraps data about latest news from financial
news website [seekingalpha.com].

## Features

Collects data about latest financial news and their impact
on current stock prices. Article data being collected:
- article titles
- link to each article
- article id on the site
- stock price change
- date and time of stock price change measurement
- stock ticker symbol
- date and time of article being posted
- article's author


This text you see here is *actually- written in Markdown! To get a feel
for Markdown's syntax, type some text into the left window and
watch the results in the right.

## Installation and usage

Install [python 3](https://www.python.org/downloads/) and
then the required python packages:

```sh
pip install -r requirements.txt
```

Make sure your local MySQL server is turned on and then configure
(just open and review) the `conf.json` and `mysql_connector.json`
files and finally run

```sh
pyhton3 main.py
```

## Settings

You can change various program setting before execution by editing
config files `conf.json` and `mysql_connector.json` or by providing
CLI commands.

Here is the explanation of the variables and CLI commands.

### conf.json file

It is the file of general program setting. Here is an example:

```json
{
    "DEBUG_LOG_LEVEL": 20,
    "DEPLOYMENT_LOG_LEVEL": 20,
    "DEBUG_MODE": true,
    "URL": "https://seekingalpha.com/market-news?page=",
    "DEPLOYMENT_NUMBER_OF_PAGES": 2,
    "DEBUG_NUMBER_OF_PAGES": 1,
    "DEBUG_NUMBER_OF_URLS": 5,
    "PARALLEL": true,
    "//00_comment": "Logging_levels:",
    "//01_comment": "DEBUG=10",
    "//02_comment": "INFO=20",
    "//03_comment": "WARN=30",
    "//04_comment": "ERROR=40",
    "//05_comment": "CRITICAL=50."
}
```

* `"DEBUG_MODE"` is the switcher between debug and deployment program scenatious.
* `"DEBUG_LOG_LEVEL"` and `"DEPLOYMENT_LOG_LEVEL"` - the levels
of logging in corresponding scenarios.
* `"DEBUG_NUMBER_OF_PAGES"` and `"DEPLOYMENT_NUMBER_OF_PAGES"` - the number
of main pages to scrap in corresponding scenarios.
* `"DEBUG_NUMBER_OF_URLS"` is the number of news articles to scrap and show.
Used only in debug mode.
* `"URL"` - the link to first news page of seekingalpha.com 
* `"PARALLEL"` - the switcher to parallel approach of web scraping

And the rest is just a note on debug levels for user comfort.

### mysql_connector.json file

This is the file of database settings. Here is an example:

```json
{
  "USER_NAME": "root",
  "PASSWORD": "root",
  "COMMAND_1": "DROP DATABASE IF EXISTS market;",
  "COMMAND_2": "CREATE DATABASE IF NOT EXISTS market;", 
  "COMMAND_3": "DROP TABLE IF EXISTS stock;",
  "COMMAND_4": "DROP TABLE IF EXISTS article;",
  "COMMAND_5": "DROP TABLE IF EXISTS author;",
  "COMMAND_6": "CREATE TABLE IF NOT EXISTS author (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255));",
  "COMMAND_7": "CREATE TABLE IF NOT EXISTS article (id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(1000), link VARCHAR(1000), datetime_posted DATETIME, author_id INT, FOREIGN KEY (author_id) REFERENCES author(id));",
  "COMMAND_8": "CREATE TABLE IF NOT EXISTS stock (id INT AUTO_INCREMENT PRIMARY KEY, ticker_symbol VARCHAR(50), price_change DECIMAL(10, 2), datetime_change DATETIME, article_id INT, FOREIGN KEY (article_id) REFERENCES article(id));"
}
```

Username, passwords and command to execute.
The commands will be executed one-by-one in a loop.
It's recommended to keep their naming style and order.

### CLI arguments

User can also provide some CLI arguments.
Most of them replace the ones provided in the `conf.json` file.

Here is the help message.

```sh
usage: main.py [-h] [-c CONFIG_FILE] [-l LOG_FILE]
               [--debug-log-level {10,20,30,40,50}]
               [--deployment-log-level {10,20,30,40,50}] [-d DEBUG_MODE]
               [--url URL] [--debug_number-of-pages DEBUG_NUMBER_OF_PAGES]
               [--deployment-number-of-pages DEPLOYMENT_NUMBER_OF_PAGES]
               [--debug-number-of-urls DEBUG_NUMBER_OF_URLS] [-p]

Scrap info from "seeking alpha" site

options:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        Path to the .json config file to use
  -l LOG_FILE, --log-file LOG_FILE
                        Name of log file
  --debug-log-level {10,20,30,40,50}
                        Log level in debug mode, integer. Possible choices: *
                        DEBUG=10 * INFO=20 * WARN=30 * ERROR=40 * CRITICAL=50
  --deployment-log-level {10,20,30,40,50}
                        Log level in deployment mode, integer. Possible
                        choices: * DEBUG=10 * INFO=20 * WARN=30 * ERROR=40 *
                        CRITICAL=50
  -d DEBUG_MODE, --debug-mode DEBUG_MODE
                        Switcher between dev (debug) and prod (deployment)
                        scenarios.
  --url URL             URL of the main news page. Must ends with '?page='
  --debug_number-of-pages DEBUG_NUMBER_OF_PAGES
                        Number of news main pages to scrap in debug mode
  --deployment-number-of-pages DEPLOYMENT_NUMBER_OF_PAGES
                        Number of news main pages to scrap in deployment mode
  --debug-number-of-urls DEBUG_NUMBER_OF_URLS
                        Number of articles to save and show in debug mode(used
                        only in debug mode)
  -p, --parallel        Run the scraping in parallel using grequests.
```

Tell us if you find the explanations above not clear!

We also underline that there is a possibility to use non-default
json files instead of `conf.json` by using `-l` or `-log-file` CLI argument as follows:

```sh
pyhton3 main.py -c conf_2.json
```

## Database structure

The program is designed to save data to relational database of the following
structure provided in the picture below.

![alt text](ERD.png "ERD")

## Contributors

This project is brought to you
by [Alexander Makienkov][alexM_li] and [Maxim Shatsky][maxs_li].

> Special thanks to our ITC friends and our great teachers [Felipe][Felipe_gh],
> [Yoni K][YoniK_gh], Yoni M, Merav and the rest of ITC staff!
>

Want to contribute? You are welcome to connect us,
create issues and PR the project!

Thank you for visiting!
-----------------------

### Max Shatsky: [GitHub][maxs_gh] , [LinkedIn][maxs_li]

### Alex Makienkov: [GitHub][alexM_gh] , [LinkedIn][alexM_li]


[//]: # (reference links)

   [maxs_gh]: <https://github.com/maxshatsky>
   [maxs_li]: <https://www.linkedin.com/in/maxshatsky/>
   [alexM_gh]: <https://github.com/makienkov> 
   [alexM_li]: <https://www.linkedin.com/in/alexander-makienkov/>
   [git-repo-url]: <https://github.com/makienkov/ITC0223_project_1>
   [seekingalpha.com]: <https://seekingalpha.com/> 
   [YoniK_gh]: <https://github.com/yoni2k>
   [Felipe_gh]: <https://github.com/felipemalbergier>
