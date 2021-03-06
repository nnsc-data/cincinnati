import math
import numpy as np
import pandas as pd
from copy import deepcopy
from itertools import combinations
from lib_cinci.db import uri
from scipy import stats
from itertools import combinations
from sklearn.linear_model import LinearRegression
from sklearn_evaluation.metrics import precision_at
from sqlalchemy import create_engine

'''
    This file provides utility functions to evaluate
    model predictions
'''

def add_flags_to_predictions_df(df):
    '''
        Given a data frame with the following format:
            - Indexes: parcel_id, inspection_date
            - Columns: prediction, viol_outcome

        Attach columns with various metrics and flags
    '''
    #Copy df to avoid overwriting
    df = deepcopy(df)

    #Calculate precisions at 1 and 10 percent
    prec1, cutoff1 = precision_at(df.viol_outcome, df.prediction, percent=0.01)
    prec10, cutoff10 = precision_at(df.viol_outcome, df.prediction, percent=0.1)

    #Add columns
    df['top_1'] = df.prediction.map(lambda x: x>= cutoff1)
    df['top_10'] = df.prediction.map(lambda x: x>= cutoff10)
    df['tp_top_1'] = df.top_1 & df.viol_outcome
    df['tp_top_10'] = df.top_10 & df.viol_outcome
    df['fp_top_1'] = df.top_1 & ~df.viol_outcome
    df['fp_top_10'] = df.top_10 & ~df.viol_outcome
    return df

def add_parcel_type(df):
    '''
        Returns a copy of the original DataFrame with one extra column
        indicating if the parcel is residential
    '''
    def is_residential(property_class):
        if int(property_class) == 423 or 500 <= int(property_class) <= 599:
            return True
        return False

    e = create_engine(uri)
    query = ("SELECT parcels.parcelid AS parcel_id, parcels.class "
            "FROM shape_files.parcels_cincy AS parcels")
    parcel_type = pd.read_sql(query, e, index_col='parcel_id')
    parcel_type["is_residential"] = parcel_type["class"].apply(is_residential)
    return df.join(parcel_type[['is_residential']])


def add_inspections_results_for(df, start, end):
    '''
        Returns a copy of the original data frame with three new columns
        inspections, violations and nonviolations which is the count for
        such events between start_year and end_year
    '''
    e = create_engine(uri)
    query = '''
        WITH sub AS(
            SELECT parcel_id, inspection_date, 
            MAX(CASE WHEN viol_outcome = 1 THEN 1 ELSE 0 END) viol_outcome 
            FROM features.parcels_inspections AS insp
            WHERE
                insp.inspection_date >= %(start)s
            AND
                insp.inspection_date <= %(end)s
            GROUP BY 
               parcel_id, inspection_date
            )

        SELECT  parcel_id,
            SUM(CASE WHEN viol_outcome = 1 THEN 1 ELSE 0 END) violations,
            SUM(CASE WHEN viol_outcome = 0 THEN 1 ELSE 0 END) non_violations,
            COUNT(*) AS inspections
        FROM sub GROUP BY parcel_id;
    '''
    insp_results = pd.read_sql(query, e, index_col='parcel_id',
                               params={'start': start, 'end': end})
    return df.join(insp_results)


def add_latlong_to_df(df):
    '''
        Return a predictions data frame with latitude and longitude columns
        for each parcel. The DatFrame passed as parameter is expected to
        have a parcel_id index.

        This method is not memory efficient since it loads
        all parcels into memory, but it makes easier to retrieve lat,long.
        Use it responsibly.
    '''
    e = create_engine(uri)
    parcels = pd.read_sql_table('parcels_cincy', e,
        schema='shape_files',
        columns=['latitude', 'longitude'],
        index_col='parcelid')
    parcels.index.rename('parcel_id', inplace=True)
    return df.join(parcels)

def load_violations_for(start_year, end_year=None):
    '''
        Load violations that happened between start_year and end_year,
        returns a DataFrame with parcel_id, inspection_date, latitude, 
        longitude. Takes data from features schema, which has all
        inspections done.
    '''
    #If only one parameter is passed, set end_year
    #to the value of start_year
    end_year = start_year if end_year is None else end_year
    e = create_engine(uri)
    q='''
        SELECT
            insp.parcel_id, insp.inspection_date,
            parc.latitude, parc.longitude
        FROM features.parcels_inspections AS insp
        JOIN shape_files.parcels_cincy AS parc
        ON insp.parcel_id=parc.parcelid
        WHERE viol_outcome=1
        AND EXTRACT(YEAR FROM inspection_date)>=%(start_year)s
        AND EXTRACT(YEAR FROM inspection_date)<=%(end_year)s
    '''
    viol = pd.read_sql(q, e,
        #columns=['latitude', 'longitude'],
        params={'start_year':start_year
        , 'end_year':end_year})
    viol.set_index(['parcel_id', 'inspection_date'], inplace=True)
    return viol

def load_inspections_for(start_year, end_year=None):
    '''
        Load inspections that happened between start_year and end_year,
        returns a DataFrame with parcel_id, inspection_date, latitude, 
        longitude. Takes data from features schema, which has all
        inspections done.
    '''
    #If only one parameter is passed, set end_year
    #to the value of start_year
    end_year = start_year if end_year is None else end_year
    e = create_engine(uri)
    q='''
        SELECT
            insp.parcel_id, insp.inspection_date, insp.viol_outcome,
            parc.latitude, parc.longitude
        FROM features.parcels_inspections AS insp
        JOIN shape_files.parcels_cincy AS parc
        ON insp.parcel_id=parc.parcelid
        AND EXTRACT(YEAR FROM inspection_date)>=%(start_year)s
        AND EXTRACT(YEAR FROM inspection_date)<=%(end_year)s
    '''
    inspections = pd.read_sql(q, e,
        params={'start_year':start_year, 'end_year':end_year})
    inspections.set_index(['parcel_id', 'inspection_date'], inplace=True)
    return inspections

def load_one_inspection_per_parcel(start, end=None, which='last'):
    '''
        Function to get inspections results for parcels in Cincinnati. 
        
        Takes inputs start and end demarcating the validation window.
        If end is not specified, default will be today's date (i.e. all inspections after start).
        Start and end should be in datetime date format e.g. '2016-01-01'.
        
        Returns a DataFrame with one row for each parcel in
        features.parcels_inspections for the period between start and end.
        
        The DataFrame is indexed on parcel_id and has columns
        inspection_date, viol_outcome (binary), and viol_count (integer-valued).
        
        If there are multiple inspections for a given parcel-period pair,
        inspection_date will be the earliest date in the window,
        viol_outcome will be 1 if there was at least one violation (else 0),
        and viol_count will be summed over all inspections.

    '''

    query= '''
        WITH sub AS(
            SELECT *
            FROM features.parcels_inspections AS insp
            WHERE
                insp.inspection_date>=%(start)s
            AND 
                insp.inspection_date<=%(end)s 
            
        ),
        earliest AS(
            SELECT *,
               ROW_NUMBER() OVER(PARTITION BY sub.parcel_id ORDER BY sub.inspection_date ASC) AS rn,
               SUM(viol_outcome) OVER(PARTITION BY sub.parcel_id) AS viol_count
            FROM sub
        ),
        
        any_last AS(
            SELECT parcel_id, inspection_date, rn, viol_count,
                   --replace viol_outcome
                   CASE WHEN viol_count > 0 THEN 1 ELSE 0 END AS viol_outcome
            FROM earliest
        )
        
        SELECT insp.parcel_id, insp.viol_outcome, insp.viol_count
            FROM any_last AS insp
            WHERE rn = 1
    '''

    #If end is not provided, use today
    end = date.today().strftime('%Y-%m-%d') if end is None else end
    e = create_engine(uri)

    inspections_df = pd.read_sql(query, e,
        params={'start':start, 'end':end})
    inspections_df.set_index(['parcel_id'], inplace=True)
    return inspections_df

def add_percentile_column(df, column_name):
    '''
        Given a DataFrame and a column_name
       return a new DataFrame with a new column including
       the percentile for the value in column_name 
    '''
    df = deepcopy(df)
    col_vals = df[column_name]
    perc_col_name = '{}_percentile'.format(column_name)
    df[perc_col_name] = [stats.percentileofscore(col_vals, value, 'rank') for value in col_vals]
    return df

def distance_on_unit_sphere(coords1, coords2):
    lat1, long1 = coords1
    lat2, long2 = coords2
    # Convert latitude and longitude to
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0

    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians

    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians
    # Compute spherical distance from spherical coordinates.
    # For two locations in spherical coordinates
    # (1, theta, phi) and (1, theta', phi')
    # cosine( arc length ) =
    # sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) +
    math.cos(phi1)*math.cos(phi2))

    if cos > 1.0:
        cos = 1.0
    if cos < -1.0:
        cos = -1.0

    arc = math.acos( cos )
    # Remember to multiply arc by the radius of the earth
    # in your favorite set of units to get length.
    return arc*6373.0

def avg_dist(m):
    #Get coordinates as tuples
    coords = list(m[['latitude', 'longitude']].itertuples(index=False, name=None))
    #Get every combination of coordinates pairs
    pairs = combinations(coords, 2)
    #Calculate distance for every pair
    dists = [distance_on_unit_sphere(*p) for p in pairs]
    return np.mean(dists)

def density_rsquare(df, mdist, months):
    """
    Return the R^2 for a linear regression that uses 
    neighborhood-level information to fit the predicted scores
    of a model.
    Args:
        df (pd.DataFrame): A dataframe that has columns 'prediction',
                           and columns 'violation_rate_Xm_Ymonths' and
                           'inspection_density_Xm_Ymonths', where X and Y
                           are given by the following two arguments:
        mdist (int): The spatial aggregation window for the neighborhood 
                     metrics. Corresponding columns must be present in df.
        months: (int): The temporal aggregation window for the neighborhood
                       metrics. Corresponding columns must be present in df.
    Returns (float): The R-square for a linear regression that fits 
                     df['prediction'], using as features 
                     df['inspection_density_Xm_Ymonths'] and
                     df['violation_rate_Xm_Ymonths'], and their interaction.
    """

    insp_col = 'inspection_density_{mdist}m_{months}months'.format(mdist=mdist, 
                                                            months=months)
    viol_col = 'violation_rate_{mdist}m_{months}months'.format(mdist=mdist, 
                                                        months=months)

    if not ((insp_col in df.columns) and (viol_col in df.columns)):
        raise ValueError("The corresponding inspection_density or violation_rate "
                "column for %sm and %smonths is missing."%(str(mdist), str(months)))

    if not 'prediction' in df.columns:
        raise ValueError("The 'prediction' column is missing.")

    mydf = df.loc[:,[insp_col, viol_col, 'prediction']].copy()

    # if the model wasn't able to fit a datapoint, we drop that row
    mydf = mydf.dropna(subset=['prediction'])
    
    # we impute with the median, as the input data are ratios
    mydf = mydf.fillna(mydf.median())

    y = mydf.pop('prediction')

    # get the interaction term
    mydf['interaction'] = mydf.prod(axis=1)

    # fit the linear regression
    linreg = LinearRegression()
    linreg.fit(X=mydf, y=y)

    # calculate the R^2
    r2 = linreg.score(X=mydf, y=y)

    return r2

