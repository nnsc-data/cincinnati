--CRIME
CREATE TEMPORARY TABLE new_crime AS(
    SELECT event.*, addr.id AS address_id
    FROM crime AS event
    LEFT JOIN address AS addr
    USING (address)
);

DROP TABLE IF EXISTS crime;

CREATE TABLE crime AS(
    SELECT * FROM new_crime
);

--FIRE
CREATE TEMPORARY TABLE new_fire AS(
    SELECT event.*, addr.id AS address_id
    FROM fire AS event
    LEFT JOIN address AS addr
    USING (address)
);

DROP TABLE IF EXISTS fire;

CREATE TABLE fire AS(
    SELECT * FROM new_fire
);

--SALES
CREATE TEMPORARY TABLE new_sales AS(
    SELECT event.*, addr.id AS address_id
    FROM sales AS event
    LEFT JOIN address AS addr
    USING (address)
);

DROP TABLE IF EXISTS sales;

CREATE TABLE sales AS(
    SELECT * FROM new_sales
);