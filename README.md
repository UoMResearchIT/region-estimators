# region_estimators package

region_estimators is a Python library to calculate regional estimations of scalar quantities, based on some known scalar quantities at specific locations.
For example, estimating the NO2 (pollution) level of a postcode/zip region, based on sensor data nearby.  
This first version of the package is initialised with 2 estimation methods: 
1. Diffusion: look for actual data points in gradually wider rings, starting with sensors within the region, and then working in rings outwards, until sensors are found. If more than one sensor is found at the final stage, it takes the mean.
2. Simple Distance measure: This is a very basic implementation... Find the nearest sensor to the region and use that value. 
If sensors exist within the region, take the mean.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install region_estimators.

```bash
pip install region_estimators
```

## Usage

```python
>>> from shapely import wkt
>>> import pandas as pd
>>> from region_estimators import RegionEstimatorFactory


# Prepare input files
>>> df_regions = pd.read_csv('/path/to/file/df_regions.csv', index_col='region_id')
>>> df_sensors = pd.read_csv('/path/to/file/df_sensors.csv', index_col='sensor_id')
>>> df_actuals = pd.read_csv('/path/to/file/df_actuals.csv')
>>> df_regions['geometry'] = df_regions.apply(lambda row: wkt.loads(row.geometry), axis=1)

# Create estimator
>>> estimator = RegionEstimatorFactory.region_estimator('diffusion', df_sensors, df_regions, df_actuals)

# Make estimations
>>> estimator.get_estimations('AB', '2017-07-01')
>>> estimator.get_estimations(None, '2018-08-15')
>>> estimator.get_estimations('AB', None)
#WARNING! - estimator.get_estimates(None, None) will calculate estimates for every region at every timestamp.
>>> estimator.get_estimations(None, None) 


##### Details of region_estimators classes / methods used above: #####

# Call RegionEstimatorFactory.region_estimator
# Reguired inputs: 
# 	method_name (string): 	the estimation method. For example, in the first version 
# 				the options are 'diffusion' or 'distance-simple'


# 	3 pandas.Dataframe objects:

	'''
    sensors: list of sensors as pandas.DataFrame (one row per sensor)
	    Required columns:
                'sensor_id' (INDEX): identifier for sensor (must be unique to each sensor)
                'latitude' (numeric): latitude of sensor location
                'longitude' (numeric): longitude of sensor location
            Optional columns:
                'name' (string): Human readable name of sensor

    regions: list of regions as pandas.DataFrame  (one row per region)
        Required columns:
            'region_id' (INDEX): identifier for region (must be unique to each region)
            'geom' (shapely.wkt/geom.wkt):  Multi-polygon representing regions location and shape.

    actuals: list of actual sensor values as pandas.DataFrame (one row per timestamp)
        Required columns:
            'timestamp' (string): timestamp of actual reading
            'sensor': ID of sensor which took actual reading (must match with a sensors.sensor_id
                in sensors (in value and type))
            'value' (numeric): scalar value of actual reading
	'''

estimator = RegionEstimatorFactory.region_estimator(method_name, df_sensors, df_regions, df_actuals)


# Call RegionEstimatorFactory.get_estimations
# Required inputs: 
# 	region_id:  region identifier (string (or None to get all regions))
# 	timestamp:  timestamp identifier (string (or None to get all timestamps))
#	
#	WARNING! - estimator.get_estimates(None, None) will calculate every region at every timestamp.

result = estimator.get_estimations('AB', '2018-08-15')

# result is json list of dicts, each with
#                i) 'region_id'
#                ii) calculated 'estimates' (list of dicts, each containing 'value', 'extra_data', 'timestamp')
#			('value' is estimated value and 'extra_data' is extra info about estimation calculation.)

```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
[MIT](https://opensource.org/licenses/MIT)
