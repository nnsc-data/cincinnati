PATH_TO_MODEL="../blight_risk_prediction/"
PATH_TO_EXP="$ROOT_FOLDER/experiments/"

$PATH_TO_MODEL/model.py -c $PATH_TO_EXP/all_freqs_features_1000m_3months.yaml
$PATH_TO_MODEL/model.py -c $PATH_TO_EXP/all_freqs_features_1000m_6months.yaml
$PATH_TO_MODEL/model.py -c $PATH_TO_EXP/all_freqs_features_700m_3months.yaml
$PATH_TO_MODEL/model.py -c $PATH_TO_EXP/all_freqs_features_700m_6months.yaml
$PATH_TO_MODEL/model.py -c $PATH_TO_EXP/all_freqs_features_400m_3months.yaml
$PATH_TO_MODEL/model.py -c $PATH_TO_EXP/all_freqs_features_400m_6months.yaml

#$PATH_TO_MODEL/model.py -c $PATH_TO_EXP/all_freqs_features_1000m_3months.yaml
#$PATH_TO_MODEL/model.py -c $PATH_TO_EXP/all_freqs_features_1000m_6months.yaml
#$PATH_TO_MODEL/model.py -c $PATH_TO_EXP/all_freqs_features_1000m_9months.yaml