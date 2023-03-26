DROP DATABASE IF EXISTS market;
CREATE DATABASE IF NOT EXISTS market;
USE market;

SELECT 'CREATING DATABASE STRUCTURE' as 'INFO';

DROP TABLE IF EXISTS stock,
                     author,
                     article;

CREATE TABLE `article` (
  `article_id` int PRIMARY KEY,
  `title` varchar(1000),
  `link` varchar(1000),
  `date_posted` date,
  `time_posted` time,
  `author_id` int,
  `ticker_symbol` varchar(50)
);

CREATE TABLE `stock` (
  `ticker_symbol` varchar(50) PRIMARY KEY,
  `price_change` decimal,
  `date_change` date,
  `time_change` time,
  `article_id` int
);

CREATE TABLE `author` (
  `author_id` int PRIMARY KEY,
  `name` varchar(255)
);

ALTER TABLE `article` ADD FOREIGN KEY (`author_id`) REFERENCES `author` (`author_id`);

ALTER TABLE `article` ADD FOREIGN KEY (`ticker_symbol`) REFERENCES `stock` (`ticker_symbol`);

ALTER TABLE `stock` ADD FOREIGN KEY (`article_id`) REFERENCES `article` (`article_id`);

