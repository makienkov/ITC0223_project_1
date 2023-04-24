DROP DATABASE IF EXISTS market;
CREATE DATABASE IF NOT EXISTS market;
USE market;

SELECT 'CREATING DATABASE STRUCTURE' as 'INFO';

DROP TABLE IF EXISTS stock,
                     author,
                     article,
                     prices;

CREATE TABLE `Article` (
  `id` int PRIMARY KEY,
  `title` varchar(255),
  `link` varchar(255),
  `datetime_posted` datetime,
  `author_id` int
);

CREATE TABLE `Stock` (
  `id` int PRIMARY KEY,
  `ticker_symbol` varchar(255),
  `price_change` decimal,
  `datetime_change` datetime,
  `article_id` int
);

CREATE TABLE `Author` (
  `id` int PRIMARY KEY,
  `name` varchar(255)
);

CREATE TABLE `Prices` (
  `id` int PRIMARY KEY,
  `ticker_symbol_id` int,
  `datetime` datetime,
  `open` decimal,
  `high` decimal,
  `low` decimal,
  `close` decimal,
  `volume` int
);

ALTER TABLE `Author` ADD FOREIGN KEY (`id`) REFERENCES `Article` (`author_id`);

ALTER TABLE `Stock` ADD FOREIGN KEY (`article_id`) REFERENCES `Article` (`id`);

ALTER TABLE `Prices` ADD FOREIGN KEY (`ticker_symbol_id`) REFERENCES `Stock` (`id`);


