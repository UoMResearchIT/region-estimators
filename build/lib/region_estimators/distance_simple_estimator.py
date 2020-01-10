import pandas as pd
import geopandas as gpd

from region_estimators.region_estimator import RegionEstimator


class DistanceSimpleEstimator(RegionEstimator):

    def __init__(self, sensors, regions, actuals):
        super(DistanceSimpleEstimator, self).__init__(sensors, regions, actuals)

    class Factory:
        def create(self, sensors, regions, actuals):
            return DistanceSimpleEstimator(sensors, regions, actuals)



    def get_estimate(self, timestamp, region_id):
        """  Find estimations for a region and timestamp using the simple distance method: value of closest actual sensor

            :param timestamp:  timestamp identifier (string)
            :param region_id: region identifier (string)

            :return: tuple containing
                i) estimate
                ii) dict: {'closest_sensor_ids': [IDs of closest sensor(s)]}

        """
        result = None, {'closest_sensor_data': None}

        # Get the actual values

        df_actuals = self.actuals.loc[
            (self.actuals['sensor'].isin(self.sensors.index.tolist())) &
            (self.actuals['timestamp'] == timestamp) &
            (self.actuals['value'].notnull())
        ]


        df_sensors = self.sensors.reset_index().rename(columns={"sensor_id": "sensor"})

        df_actuals = pd.merge(left=df_actuals,
                           right= df_sensors,
                           on='sensor',
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
                closest_values_mean = closest_sensors['value'].mean(axis=0)

                if 'name' in list(closest_sensors.columns):
                    closest_sensors_result = list(closest_sensors['name'])
                else:
                    closest_sensors_result = list(closest_sensors.iloc[:,1])

                result = closest_values_mean, {'closest_sensors': closest_sensors_result}

        return result
