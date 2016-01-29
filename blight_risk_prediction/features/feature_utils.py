import pandas as pd
from string import Template
import os
#This file provides generic functions
#to generate spatiotemporal features

def create_events_3months_table(con, schema, table_name, date_column):
    path_to_template = os.path.join(os.environ['ROOT_FOLDER'],
                    'blight_risk_prediction',
                    'features',
                    'events_xmonths.template.sql')
    #Load template with SQL statement
    with open(path_to_template, 'r') as f:
        sql_script = Template(f.read())
    #Replace values in template
    sql_script = sql_script.substitute(TABLE_NAME=table_name, DATE_COLUMN=date_column)
    #Run the code using the connection
    #this is going to take a while
    try:
        con.cursor().execute(sql_script)
    except Exception, e:
        con.rollback()
        con.cursor().execute("SET SCHEMA '{}'".format(schema))
        print 'Failed to create 3 month table. {}'.format(e)

def compute_frequency_features(con, table_name, columns, ids=['parcel_id', 'inspection_date']):
    ids = [ids] if type(ids)==str else ids
    columns = [columns] if type(columns)==str else columns

    df = pd.read_sql('SELECT * FROM events_3months_{}'.format(table_name), con)
    ids_series = [df[i] for i in ids]
    cols_series = [df[i] for i in columns]
    #Group by parcel_id and inspection_date. Make columns with counts
    #for some columns
    cross = pd.crosstab(ids_series, cols_series)
    #Rename columns to avoid capital letters and spaces
    cross.columns = cross.columns.map(lambda s: s.replace(' ', '_').lower())
    return cross