from region_estimators.region_estimator import RegionEstimator
import pandas as pd


class ConcentricRegionsEstimator(RegionEstimator):
    MAX_RING_COUNT_DEFAULT = float("inf")

    def __init__(self, estimation_data=None,  verbose=RegionEstimator.VERBOSE_DEFAULT,
                 max_processors=RegionEstimator.MAX_NUM_PROCESSORS):
        super(ConcentricRegionsEstimator, self).__init__(estimation_data, verbose, max_processors)
        self.__set_region_neighbours()
        self._max_ring_count = ConcentricRegionsEstimator.MAX_RING_COUNT_DEFAULT

    class Factory:
        def create(self, estimation_data, verbose=RegionEstimator.VERBOSE_DEFAULT,
                 max_processors=RegionEstimator.MAX_NUM_PROCESSORS):
            return ConcentricRegionsEstimator(estimation_data, verbose, max_processors)

    @property
    def max_ring_count(self):
        return self._max_ring_count

    @max_ring_count.setter
    def max_ring_count(self,  new_count=MAX_RING_COUNT_DEFAULT):
        """  Set the maximum ring count of the concentric_regions estimation procedure

                   :param new_count:
                    the maximum number of rings to be allowed during concentric_regions (integer, default=MAX_RING_COUNT_DEFAULT)
        """

        self._max_ring_count = new_count

    def get_estimate(self, measurement, timestamp, region_id, ignore_site_ids=[]):
        """  Find estimations for a region and timestamp using the concentric_regions rings method

            :param measurement: measurement to be estimated (string, required)
            :param region_id: region identifier (string)
            :param timestamp:  timestamp identifier (string)
            :param ignore_site_ids: site id(s) to be ignored during the estimations

            :return: tuple containing result and dict: {"rings": [The number of concentric_regions rings required]}
        """
        if self.verbose > 0:
            print('\n### Getting estimates for region {}, measurement {} at date {} ###\n'.format(
                region_id, measurement, timestamp))

        # Check sites exist (in any region) for this measurement/timestamp
        if self.estimation_data.site_datapoint_count(measurement, timestamp, ignore_site_ids=ignore_site_ids) == 0:
            if self.verbose > 0:
                print('No sites exist for region {}, measurement {} at date {}'.format(
                    region_id, measurement, timestamp))
            return None, {"rings": None}

        if self.verbose > 1:
            print('sites exist for region {}, measurement {} at date {}'.format(region_id, measurement, timestamp))

        # Check region is not an island (has no touching adjacent regions) which has no sites within it
        # If it is, return null
        region_sites = set(self.regions.loc[region_id]['sites']) - set(ignore_site_ids)
        if len(region_sites) == 0 and len(self.estimation_data.get_adjacent_regions([region_id])) == 0:
            if self.verbose > 0:
                print('Region {} is an island and does not have sites, so can\'t do concentric_regions'.format(region_id))
            return None, {"rings": None}

        if self.verbose > 1:
            print('Region {} is not an island'.format(region_id))

        # Create an empty list for storing completed regions
        regions_completed = []

        # Recursively find the sites in each concentric_regions ring (starting at 0)
        if self.verbose > 0:
            print('Beginning recursive region estimation for region {}, timestamp: {}'.format(region_id, timestamp))

        return self.__get_concentric_regions_estimate_recursive(measurement, [region_id], timestamp, 0, regions_completed,
                                                       ignore_site_ids)

    def __get_concentric_regions_estimate_recursive(self, measurement, region_ids, timestamp, diffuse_level, regions_completed,
                                           ignore_site_ids=[]):
        # Find all sites in regions
        sites = self.estimation_data.get_regions_sites(region_ids, ignore_site_ids)

        # Get values from sites
        if self.verbose > 0:
            print('obtaining values from sites')
        actuals = self.actuals.loc[(self.actuals['timestamp'] == timestamp) & (self.actuals['site_id'].isin(sites))]

        result = None
        if len(actuals.index) > 0:
            # If readings found for the sites, take the average
            result = actuals[measurement].mean(axis=0)
            if self.verbose > 0:
                print('Found result (for regions: {}) from sites:\n {}, average: {}'.format(region_ids, actuals, result))

        if result is None or pd.isna(result):
            if self.verbose > 0:
                print('No sites found. Current ring count: {}. Max concentric_regions level: {}'.format(
                    diffuse_level, self._max_ring_count))
            # If no readings/sites found, go up a concentric_regions level (adding completed regions to ignore list)
            if diffuse_level >= self.max_ring_count:
                if self.verbose > 0:
                    print('Max concentric_regions level reached so returning null.')
                return None, {"rings": diffuse_level}

            regions_completed.extend(region_ids)
            diffuse_level += 1

            # Find the next set of regions
            next_regions = self.estimation_data.get_adjacent_regions(region_ids, regions_completed)
            if self.verbose > 0:
                print('Found next set of regions: {}.'.format(next_regions))

            # If regions are found, continue, if not exit from the process
            if len(next_regions) > 0:
                if self.verbose > 0:
                    print('Next set of regions non empty so recursively getting concentric_regions estimates for those: {}.'
                          .format(next_regions))
                return self.__get_concentric_regions_estimate_recursive(measurement,
                                                               next_regions,
                                                               timestamp,
                                                               diffuse_level,
                                                               regions_completed,
                                                               ignore_site_ids)
            else:
                if self.verbose > 0:
                    print('No next set of regions found so returning null')
                return None, {"rings": diffuse_level-1}
        else:
            if self.verbose > 0:
                print('Returning the result')
            return result, {"rings": diffuse_level}

    def __set_region_neighbours(self):
        '''
        Find all of the neighbours of each region and add to a 'neighbours' column in self.regions -
        as comma-delimited string of region_ids

        :return: No return value
        '''

        if self.verbose > 0:
            print('\ngetting all region neighbours')

        for index, region in self.regions.iterrows():
            neighbors = self.regions[self.regions.geometry.touches(region.geometry)].index.tolist()
            neighbors = filter(lambda item: item != index, neighbors)
            neighbors_str = ",".join(neighbors)
            self.regions.at[index, "neighbours"] = neighbors_str

            if self.verbose > 1:
                print('neighbours for {}: {}'.format(index, neighbors_str))
