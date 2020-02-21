#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import glob
from pandas.io.json import json_normalize
import json
import os

# Set directories
input_dir = '../region_estimator_outputs'
output_dir = os.path.join(input_dir, 'collated')
if not os.path.exists(output_dir):
    os.mkdir(output_dir)
output_file = os.path.join(output_dir, 'estimates_new.csv')


# Get all output filenames (one for each measurement and timestamp
filenames = sorted(glob.glob(input_dir + '/*.csv'))


# Get all measurement names (from the estimation outputs file-names).
measurements = []
for filename in filenames:
    name = os.path.basename(filename)
    split_str = name.split("_")
    split_str.pop(-1)
    measurement = '_'.join(split_str)
    measurements.append(measurement)
measurements = sorted(list(set(measurements)))    


# For each measurement - concatonate the respective files into one measurement file

for measurement in measurements:
    # Do first file - and use as test/sanity-check, before looping through all files
    cur_filenames = sorted(glob.glob(input_dir + '/' + measurement + '_*.csv'))    
    df_measurement = pd.read_csv(
        cur_filenames[0], 
        index_col=['region_id','timestamp'], 
        usecols=['region_id','timestamp','measurement','value','extra_data'])
    df_measurement[measurement] = df_measurement['value']
    df_extra = json_normalize(df_measurement.extra_data.apply(json.loads))
    df_measurement['extra_rings_' + measurement] = df_extra['rings'].values
    df_measurement['extra_rings_' + measurement] = df_measurement['extra_rings_' + measurement].fillna(-1)
    df_measurement['extra_rings_' + measurement] = df_measurement['extra_rings_' + measurement].astype(int)
    df_measurement = df_measurement.drop(columns=['measurement', 'value', 'extra_data'])
    df_measurement = df_measurement.rename(columns={measurement: 'val_'+ measurement})

    # Loop through rest of files and append each
    for cur_filename in cur_filenames[1:]:        
        df_cur = pd.read_csv(
            cur_filename, 
            index_col=['region_id','timestamp'], 
            usecols=['region_id','timestamp','measurement','value','extra_data'])
        df_cur[measurement] = df_cur['value']
        df_extra = json_normalize(df_cur.extra_data.apply(json.loads))
        df_cur['extra_rings_' + measurement] = df_extra.iloc[:,0].values
        df_cur['extra_rings_' + measurement] = df_cur['extra_rings_' + measurement].fillna(-1)
        df_cur['extra_rings_' + measurement] = df_cur['extra_rings_' + measurement].astype(int)
        df_cur = df_cur.drop(columns=['measurement', 'value', 'extra_data'])
        df_cur.rename(columns={measurement: 'val_'+measurement}, inplace=True)
    
        df_measurement = df_measurement.append(df_cur)
    df_measurement.to_csv(os.path.join(output_dir, measurement + '.csv'))


# Go through each of the newly created measurement files and join into a single file
measurement_filenames = sorted(glob.glob(output_dir + '/*.csv'))

# Do first file - and use as test/sanity-check, before looping through all files 
df_result = pd.read_csv(
    measurement_filenames[0], 
    index_col=['region_id','timestamp'])

# Loop through rest of files and join each
for filename in measurement_filenames[1:]:
    print('Filename:', os.path.basename(filename))
    df_cur = pd.read_csv(
        filename, 
        index_col=['region_id','timestamp'])    
    df_result = df_result.join(df_cur)
    
df_result.to_csv(output_file)
