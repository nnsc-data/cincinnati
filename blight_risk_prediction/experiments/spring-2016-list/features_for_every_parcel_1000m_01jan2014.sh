#Generate spatiotemporal features for features_01jan2014 table
#with the following spatiotemporal parameters:
#3months, 6months, 9months
PATH_TO_BOT="$ROOT_FOLDER/blight_risk_prediction/features"

#non-spatiotemporal features
$PATH_TO_BOT/featurebot.py -d 01jan2014 -f tax,crime_agg,named_entities,house_type,parc_area,parc_year,census_2010

$PATH_TO_BOT/featurebot.py -d 01jan2014 -f three11,permits,crime,fire,sales -m 3 -md 1000
$PATH_TO_BOT/featurebot.py -d 01jan2014 -f three11,permits,crime,fire,sales -m 6 -md 1000
$PATH_TO_BOT/featurebot.py -d 01jan2014 -f three11,permits,crime,fire,sales -m 9 -md 1000