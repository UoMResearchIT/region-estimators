#!/usr/bin/env python
# coding: utf-8

import sys
import pandas as pd
import glob
import os

# Get parameters
input_dir = sys.argv[1]

# Set directories

output_dir = os.path.join(input_dir, 'collated')
if not os.path.exists(output_dir):
    os.mkdir(output_dir)
output_file = os.path.join(output_dir, 'estimates_new.csv')

# Go through each of the newly created measurement files and join into a single file

measurement_filenames = sorted(glob.glob(output_dir + '/*.csv'))

# Do first file - and use as test/sanity-check, before looping through all files 

df_result = pd.read_csv(
    measurement_filenames[0], 
    index_col=['region_id','timestamp'])

# Loop through rest
for filename in measurement_filenames[1:]:
    print('Filename:', os.path.basename(filename))
    df_cur = pd.read_csv(
        filename, 
        index_col=['region_id','timestamp'])    
    df_result = df_result.join(df_cur)
    
df_result.to_csv(output_file)
