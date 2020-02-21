from region_estimators.region_estimator import RegionEstimator
import pandas as pd

MAX_RING_COUNT_DEFAULT = float("inf")


class DiffusionEstimator(RegionEstimator):

    max_ring_count = MAX_RING_COUNT_DEFAULT

    def __init__(self, sensors, regions, actuals):
        super(DiffusionEstimator, self).__init__(sensors, regions, actuals)

    class Factory:
        def create(self, sensors, regions, actuals):
            return DiffusionEstimator(sensors, regions, actuals)


    def set_max_ring_count(self, new_count=MAX_RING_COUNT_DEFAULT):
        """  Set the maximum ring count of the diffusion estimation procedure

                   :param new_count:
                    the maximum number of rings to be allowed during diffusion (integer, default=MAX_RING_COUNT_DEFAULT)
        """

        self.max_ring_count = new_count



    def get_estimate(self, measurement, timestamp, region_id):
        """  Find estimations for a region and timestamp using the diffusion rings method

            :param measurement: measurement to be estimated (string, required)
            :param region_id: region identifier (string)
            :param timestamp:  timestamp identifier (string)

            :return: tuple containing result and dict: {'rings': [The number of diffusion rings required]}
        """

        # Check sensors exist (in any region) for this measurement/timestamp
        if not self.sensors_exist(measurement, timestamp):
            return None, {'rings': None}

        # Create an empty list for storing completed regions
        regions_completed = []

        # Recursively find the sensors in each diffusion ring (starting at 0)
        return self.__get_diffusion_estimate_recursive(measurement, [region_id], timestamp, 0, regions_completed)


    def __get_diffusion_estimate_recursive(self, measurement, region_ids, timestamp, diffuse_level, regions_completed):
        # Create an empty queryset for sensors found in regions
        sensors = []

        # Find sensors
        df_reset = pd.DataFrame(self.regions.reset_index())
        for region_id in region_ids:
            regions_temp = df_reset.loc[df_reset['region_id'] == region_id]
            if len(regions_temp.index) > 0:
                region_sensors = regions_temp['sensors'].iloc[0]
                if len(region_sensors.strip()) > 0:
                    sensors.extend(region_sensors.split(','))


        # Get values from sensors
        actuals = self.actuals.loc[(self.actuals['timestamp'] == timestamp) & (self.actuals['sensor_id'].isin(sensors))]

        result = None
        if len(actuals) > 0:
            # If readings found for the sensors, take the average
            result = actuals[measurement].mean(axis=0)

        if result is None or pd.isna(result):
            # If no readings/sensors found, go up a diffusion level (adding completed regions to ignore list)
            if diffuse_level >= self.max_ring_count:
                return None, {'rings': diffuse_level}

            regions_completed.extend(region_ids)
            diffuse_level += 1

            # Find the next set of regions
            next_regions = self.get_adjacent_regions(region_ids, regions_completed)

            # If regions are found, continue, if not exit from the process
            if (len(next_regions) > 0):
                return self.__get_diffusion_estimate_recursive(measurement,
                                                               next_regions,
                                                               timestamp,
                                                               diffuse_level,
                                                               regions_completed)
            else:
                return None, {'rings': diffuse_level}
        else:
            return result, {'rings': diffuse_level}
