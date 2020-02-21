#!/usr/bin/env python
# coding: utf-8

import sys
from shapely import wkt
import pandas as pd
from region_estimators import RegionEstimatorFactory
from slugify import slugify

# Get parameters
measurement = sys.argv[1]
timestamp = sys.argv[2]

# Load input files into pandas

df_regions = pd.read_csv('../region_estimator_inputs/df_regions.csv', index_col='region_id')
df_sensors = pd.read_csv('../region_estimator_inputs/df_sensors.csv', index_col='sensor_name')
df_actuals = pd.read_csv('../region_estimator_inputs/actuals_anns.csv')


# Set the geometry field to be the correct wkt format

df_regions['geometry'] = df_regions.apply(lambda row: wkt.loads(row.geometry), axis=1)


# create estimator

estimator = RegionEstimatorFactory.region_estimator('diffusion', df_sensors, df_regions, df_actuals)
estimator.set_max_ring_count(50) #Default was 3

# Get estimations

df_result = estimator.get_estimations(measurement, None, timestamp)

df_result.to_csv('../region_estimator_outputs/' + measurement + '_' + timestamp + '.csv', index=False)

