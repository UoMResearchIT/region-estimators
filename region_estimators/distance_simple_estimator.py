import pandas as pd
import geopandas as gpd

from region_estimators.region_estimator import RegionEstimator


class DistanceSimpleEstimator(RegionEstimator):

    def __init__(self, sensors, regions, actuals, verbose=RegionEstimator.VERBOSE_DEFAULT):
        super(DistanceSimpleEstimator, self).__init__(sensors, regions, actuals, verbose)

    class Factory:
        def create(self, sensors, regions, actuals, verbose=RegionEstimator.VERBOSE_DEFAULT):
            return DistanceSimpleEstimator(sensors, regions, actuals, verbose)


    def get_estimate(self, measurement, timestamp, region_id, ignore_sensor_ids=[]):
        """  Find estimations for a region and timestamp using the simple distance method: value of closest actual sensor

            :param measurement: measurement to be estimated (string, required)
            :param timestamp:  timestamp identifier (string)
            :param region_id: region identifier (string)
            :param ignore_sensor_ids: sensor id(s) to be ignored during the estimations

            :return: tuple containing
                i) estimate
                ii) dict: {'closest_sensor_ids': [IDs of closest sensor(s)]}

        """
        result = None, {'closest_sensor_data': None}

        # Check sensors exist (in any region) for this measurement/timestamp
        if self.sensor_datapoint_count(measurement, timestamp, ignore_sensor_ids=ignore_sensor_ids) == 0:
            return result

        # Get the actual values

        df_actuals = self.actuals.loc[
            (self.actuals['sensor_id'].isin(self.sensors.index.tolist())) &
            (~self.actuals['sensor_id'].isin(ignore_sensor_ids)) &
            (self.actuals['timestamp'] == timestamp) &
            (self.actuals[measurement].notnull())
        ]

        df_sensors = self.sensors.reset_index()

        df_actuals = pd.merge(left=df_actuals,
                           right= df_sensors,
                           on='sensor_id',
                           how='left')
        gdf_actuals = gpd.GeoDataFrame(data=df_actuals, geometry='geometry')

        # Get the closest sensor to the region
        if len(gdf_actuals) > 0:
            df_reset = pd.DataFrame(self.regions.reset_index())
            regions_temp = df_reset.loc[df_reset['region_id'] == region_id]
            if len(regions_temp.index) > 0:
                region = regions_temp.iloc[0]
            distances = pd.DataFrame(gdf_actuals['geometry'].distance(region.geometry))
            distances = distances.merge(gdf_actuals, left_index=True, right_index=True)

            # Get sensor(s) with shortest distance
            top_result = distances.sort_values(by=[0], ascending=True).iloc[0] #returns the whole row as a series

            if top_result is not None:
                closest_distance = top_result[0]
                # Take the average of all sensors with the closest distance
                closest_sensors = distances.loc[distances[0] == closest_distance]
                closest_values_mean = closest_sensors[measurement].mean(axis=0)

                #print('closest sensors:', closest_sensors) #FOR DEBUG

                if 'name' in list(closest_sensors.columns):
                    closest_sensors_result = list(closest_sensors['name'])
                else:
                    closest_sensors_result = list(closest_sensors['sensor_id'])

                result = closest_values_mean, {'closest_sensors': closest_sensors_result}

        return result
