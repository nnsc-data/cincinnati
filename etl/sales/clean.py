import pandas as pd
from dstools import data_folder
import os

path_to_data_folder = data_folder.for_file(__file__)

os.chdir(os.path.join(path_to_data_folder, 'tmp'))
print 'Working in folder: %s' % path_to_data_folder

#Load csv file
df = pd.read_csv("salesinfo.csv")

#Remove empty column
df.drop('Unnamed: 0', axis=1, inplace=True)

#Lowercase column names
df.columns = df.columns.map(lambda s: s.lower())

#Save data frame
df.to_csv('sales.csv', index=False)