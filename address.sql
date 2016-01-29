--This table is going to be used to store ALL different addresses
--in the different datasets we have, this way we will significantly reduce
--the number of distance computations
CREATE TABLE address (
    --Create an unique id
    id SERIAL PRIMARY KEY,
    --address: number and street name
    address varchar(100) NOT NULL,
    city varchar(30),
    state varchar(30),
    zip varchar(10),
    --geocoded addres, as returned from the census api
    geocoded_address varchar(100),
    latitude float8,
    longitude float8,
    --coordinates, make sure they are in the 3735 SRID
    x_coord int4,
    y_coord int4,
    --geometry
    geom geometry
);

CREATE INDEX ON address (id);
CREATE INDEX ON address USING GIST (geom);