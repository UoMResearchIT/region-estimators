from region_estimators.region_estimator import RegionEstimator
import pandas as pd


class DiffusionEstimator(RegionEstimator):
    MAX_RING_COUNT_DEFAULT = float("inf")

    def __init__(self, sensors, regions, actuals, verbose=RegionEstimator.VERBOSE_DEFAULT):
        super(DiffusionEstimator, self).__init__(sensors, regions, actuals, verbose)
        self._max_ring_count = DiffusionEstimator.MAX_RING_COUNT_DEFAULT

    class Factory:
        def create(self, sensors, regions, actuals, verbose=RegionEstimator.VERBOSE_DEFAULT):
            return DiffusionEstimator(sensors, regions, actuals, verbose)

    @property
    def max_ring_count(self):
        return self._max_ring_count

    @max_ring_count.setter
    def max_ring_count(self,  new_count=MAX_RING_COUNT_DEFAULT):
        """  Set the maximum ring count of the diffusion estimation procedure

                   :param new_count:
                    the maximum number of rings to be allowed during diffusion (integer, default=MAX_RING_COUNT_DEFAULT)
        """

        self._max_ring_count = new_count

    def get_estimate(self, measurement, timestamp, region_id, ignore_sensor_ids=[]):
        """  Find estimations for a region and timestamp using the diffusion rings method

            :param measurement: measurement to be estimated (string, required)
            :param region_id: region identifier (string)
            :param timestamp:  timestamp identifier (string)
            :param ignore_sensor_ids: sensor id(s) to be ignored during the estimations

            :return: tuple containing result and dict: {'rings': [The number of diffusion rings required]}
        """

        # Check sensors exist (in any region) for this measurement/timestamp
        if self.sensor_datapoint_count(measurement, timestamp, ignore_sensor_ids=ignore_sensor_ids) == 0:
            if self.verbose > 0:
                print('No sensors exist for region {}, measurement {} at date {}'.format(
                    region_id, measurement, timestamp))
            return None, {'rings': None}

        # Check region is not an island (has no touching adjacent regions) which has no sensors within it
        # If it is, return null
        region_sensors = set(self.regions.loc[region_id]['sensors']) - set(ignore_sensor_ids)
        if len(region_sensors) == 0 and len(self.get_adjacent_regions([region_id])) == 0:
            if self.verbose > 0:
                print('Region {} is an island and does not have sensors, so can\'t do diffusion'.format(region_id))
            return None, {'rings': None}

        # Create an empty list for storing completed regions
        regions_completed = []

        # Recursively find the sensors in each diffusion ring (starting at 0)
        if self.verbose > 0:
            print('Beginning recursive region estimation for region {}'.format(region_id))
        return self.__get_diffusion_estimate_recursive(measurement, [region_id], timestamp, 0, regions_completed,
                                                       ignore_sensor_ids)

    def __get_diffusion_estimate_recursive(self, measurement, region_ids, timestamp, diffuse_level, regions_completed,
                                           ignore_sensor_ids=[]):
        # Create an empty queryset for sensors found in regions
        sensors = []

        if self.verbose > 0:
            print('Finding sensors in region_ids')

        # Find sensors in region_ids
        df_reset = pd.DataFrame(self.regions.reset_index())
        for region_id in region_ids:
            if self.verbose > 1:
                print('Finding sensors in region {}'.format(region_id))
            regions_temp = df_reset.loc[df_reset['region_id'] == region_id]
            if len(regions_temp.index) > 0:
                region_sensors = regions_temp['sensors'].iloc[0].split(',')
                if len(region_sensors) > 0:
                    sensors.extend(region_sensors)
                    if self.verbose > 1:
                        print('Found sensors for region {}: {}'.format(region_id, sensors))
        sensors = list(set(sensors) - set(ignore_sensor_ids))

        # Get values from sensors
        if self.verbose > 0:
            print('obtaining values from sensors')
        actuals = self.actuals.loc[(self.actuals['timestamp'] == timestamp) & (self.actuals['sensor_id'].isin(sensors))]

        result = None
        if len(actuals) > 0:
            # If readings found for the sensors, take the average
            result = actuals[measurement].mean(axis=0)
            if self.verbose > 0:
                print('Found result (for regions: {}) from sensors: {}, average: {}'.format(region_ids, actuals, result))

        if result is None or pd.isna(result):
            if self.verbose > 0:
                print('No sensors found. Current ring count: {}. Max diffusion level: {}'.format(
                    diffuse_level, self._max_ring_count))
            # If no readings/sensors found, go up a diffusion level (adding completed regions to ignore list)
            if diffuse_level >= self.max_ring_count:
                if self.verbose > 0:
                    print('Max diffusion level reached so returning null.')
                return None, {'rings': diffuse_level}

            regions_completed.extend(region_ids)
            diffuse_level += 1

            # Find the next set of regions
            next_regions = self.get_adjacent_regions(region_ids, regions_completed)
            if self.verbose > 0:
                print('Found next set of regions: {}.'.format(next_regions))

            # If regions are found, continue, if not exit from the process
            if len(next_regions) > 0:
                if self.verbose > 0:
                    print('Next set of regions non empty so recursively getting diffusion estimates for those: {}.'
                          .format(next_regions))
                return self.__get_diffusion_estimate_recursive(measurement,
                                                               next_regions,
                                                               timestamp,
                                                               diffuse_level,
                                                               regions_completed,
                                                               ignore_sensor_ids)
            else:
                if self.verbose > 0:
                    print('No next set of regions found so returning null')
                return None, {'rings': diffuse_level}
        else:
            if self.verbose > 0:
                print('Returning the result')
            return result, {'rings': diffuse_level}
