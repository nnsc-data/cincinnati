#!/usr/bin/env bash
SALES_FOLDER="$DATA_FOLDER/etl/sales"
TMP_FOLDER="$DATA_FOLDER/etl/sales/tmp"

#Read variables from config file
DB_HOST=$(cat $ROOT_FOLDER'/config.yaml' | shyaml get-value db.host)
DB_USER=$(cat $ROOT_FOLDER'/config.yaml' | shyaml get-value db.user)
DB_NAME=$(cat $ROOT_FOLDER'/config.yaml' | shyaml get-value db.database)

#mkdir if not exists
mkdir -p $TMP_FOLDER

#Path to update script
UPDATE_SCRIPT=$ROOT_FOLDER/lib_cinci/data_updater/update.py
#Create diff file with entries to upload to the database
$UPDATE_SCRIPT $ROOT_FOLDER/etl/sales/update.yaml

#Clean dataset
echo 'Cleaninng data...'
python "$ROOT_FOLDER/etl/sales/clean.py"

#Geocode
echo 'Geocoding data, this may take a while...'
python "$ROOT_FOLDER/bulk_geocoder/geocode_csv.py" "$TMP_FOLDER/sales_clean.csv" "$TMP_FOLDER/sales_geocoded.csv"

#Process geocoded file
echo 'Final processing...'
python "$ROOT_FOLDER/bulk_geocoder/process_geocoded_csv.py" "$TMP_FOLDER/sales_geocoded.csv" "$TMP_FOLDER/sales_db.csv"

#Generate CREATE TABLE statement
csvsql -i postgresql --tables sales --db-schema public -d ',' "$TMP_FOLDER/sales_db.csv" > "$TMP_FOLDER/sales.sql"
#Drop table if exists
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "DROP TABLE IF EXISTS sales;"  
#Create table
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < "$TMP_FOLDER/sales.sql"  

#Upload data to the database
cat "$TMP_FOLDER/sales_db.csv" | psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\COPY public.sales FROM STDIN  WITH CSV HEADER DELIMITER ',';"

echo 'Done.'