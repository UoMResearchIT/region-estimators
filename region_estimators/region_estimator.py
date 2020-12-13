from abc import ABCMeta, abstractmethod
import geopandas as gpd
import pandas as pd
import json
import numpy as np

class RegionEstimator(object):
    """
        Abstract class, parent of region estimators (each implementing a different estimation method).
        Requires GeoPandas and Pandas
    """
    __metaclass__ = ABCMeta

    VERBOSE_DEFAULT = 0
    VERBOSE_MAX = 2

    def __init__(self, sites, regions, actuals, verbose=VERBOSE_DEFAULT):
        """
        Initialise instance of the RegionEstimator class.

        Args:
            sites: list of sites as pandas.DataFrame
                Required columns:
                    'site_id' (str or int) Unique identifier of site (of site) (will be converted to str)
                    'latitude' (float): latitude of site location
                    'longitude' (float): longitude of site location
                    'name' (string (Optional): Name of site

            regions: list of regions as pandas.DataFrame
                Required columns:
                    'region_id' (Unique INDEX)
                    'geometry' (shapely.wkt/geom.wkt)

            actuals: list of site values as pandas.DataFrame
                Required columns:
                    'timestamp' (str): timestamp of actual reading
                    'site_id': (str or int) ID of site which took actual reading - must match an index
                        value in sites. (will be converted to str)
                    [one or more value columns] (float):    value of actual measurement readings.
                                                            each column name is the name of the measurement
                                                            e.g. 'NO2'

            verbose: (int) Verbosity of output level. zero or less => No debug output

        Returns:
            Initialised instance of subclass of RegionEstimator

        """
        ### Check sites:

        assert sites.index.name == 'site_id', "sites dataframe index name must be 'site_id'"
        # (Not checking site_id data as that forms the index)
        assert 'latitude' in list(sites.columns), "There is no latitude column in sites dataframe"
        assert pd.to_numeric(sites['latitude'], errors='coerce').notnull().all(), \
            "latitude column contains non-numeric values."
        assert 'longitude' in list(sites.columns), "There is no longitude column in sites dataframe"
        assert pd.to_numeric(sites['longitude'], errors='coerce').notnull().all(), \
            "longitude column contains non-numeric values."

        ### Check regions
        # (Not checking region_id data as that forms the index)
        assert regions.index.name == 'region_id', "regions dataframe index name must be 'region_id'"
        assert 'geometry' in list(regions.columns), "There is no geometry column in regions dataframe"

        ### Check actuals
        assert 'timestamp' in list(actuals.columns), "There is no timestamp column in actuals dataframe"
        assert 'site_id' in list(actuals.columns), "There is no site_id column in actuals dataframe"
        assert len(list(actuals.columns)) > 2, "There are no measurement value columns in the actuals dataframe."

        # Check measurement columns have either numeric or null data
        for column in list(actuals.columns):
            if column not in ['timestamp', 'site_id']:
                # Check measurement does not contain numeric (nulls are OK)
                df_temp = actuals.loc[actuals[column].notnull()]
                assert pd.to_numeric(df_temp[column], errors='coerce').notnull().all(), \
                    "actuals['" + column + "'] column contains non-numeric values (null values are accepted)."

        self.verbose = verbose

        # Check that each site_id value is present in the sites dataframe index.
        # ... So site_id values must be a subset of allowed sites
        error_sites = set(actuals['site_id'].unique()) - set(sites.index.values)
        assert len(error_sites) == 0, \
            "Each site ID must match a site_id in sites. Error site IDs: " + str(error_sites)


        sites.index = sites.index.map(str)
        try:
            gdf_sites = gpd.GeoDataFrame(data=sites,
                                           geometry=gpd.points_from_xy(sites.longitude, sites.latitude))
        except Exception as err:
            raise ValueError('Error converting sites DataFrame to a GeoDataFrame: ' + str(err))

        gdf_sites = gdf_sites.drop(columns=['longitude', 'latitude'])

        try:
            gdf_regions = gpd.GeoDataFrame(data=regions, geometry='geometry')
        except Exception as err:
            raise ValueError('Error converting regions DataFrame to a GeoDataFrame: ' + str(err))

        #   actuals: Make sure value columns at the end of column list
        cols = actuals.columns.tolist()
        cols.insert(0, cols.pop(cols.index('site_id')))
        cols.insert(0, cols.pop(cols.index('timestamp')))

        actuals['site_id'] = actuals['site_id'].astype(str)

        self.sites = gdf_sites
        self.regions = gdf_regions
        self.actuals = actuals

        self.__set_site_region()
        self.__set_region_sites()



    @abstractmethod
    def get_estimate(self, measurement, timestamp, region_id, ignore_site_ids=[]):
        raise NotImplementedError("Must override get_estimate")

    @staticmethod
    def is_valid_site_id(site_id):
        '''
            Check if site ID is valid (non empty string)

            :param site_id:  (str) a site id

            :return: True if valid, False otherwise
        '''
        return site_id is not None and isinstance(site_id, str) and len(site_id) > 0

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, verbose=VERBOSE_DEFAULT):
        assert isinstance(verbose, int), "Verbose level must be an integer. (zero or less produces no debug output)"
        if verbose < 0:
            print('Warning: verbose input is less than zero so setting to zero')
            verbose = 0
        if verbose > RegionEstimator.VERBOSE_MAX:
            print('Warning: verbose input is greater than {}} so setting to {}'.format(
                RegionEstimator.VERBOSE_MAX, RegionEstimator.VERBOSE_MAX))
            verbose = RegionEstimator.VERBOSE_MAX
        self._verbose = verbose


    def get_estimations(self, measurement, region_id=None, timestamp=None, ignore_site_ids=[]):
        """  Find estimations for a region (or all regions if region_id==None) and
                timestamp (or all timestamps (or all timestamps if timestamp==None)

            :param measurement: measurement to be estimated (string - required)
            :param region_id: region identifier (string or None)
            :param timestamp:  timestamp identifier (string or None)
            :param ignore_site_ids: site id(s) to be ignored during the estimations

            :return: pandas dataframe with columns:
                'measurement'
                'region_id'
                'timestamp'
                'value' (calculated 'estimate)
                'extra_data' (json string)
        """

        # Check inputs
        assert measurement is not None, "measurement parameter cannot be None"
        assert measurement in list(self.actuals.columns), "The measurement: '" + measurement \
                                                          + "' does not exist in the actuals dataframe"

        if region_id is not None:
            df_reset = pd.DataFrame(self.regions.reset_index())
            regions_temp = df_reset.loc[df_reset['region_id'] == region_id]
            assert len(regions_temp.index) > 0, "The region_id does not exist in the regions dataframe"
        if timestamp is not None:
            df_actuals_reset = pd.DataFrame(self.actuals.reset_index())
            actuals_temp = df_actuals_reset.loc[df_actuals_reset['timestamp'] == timestamp]
            assert len(actuals_temp.index) > 0, "The timestamp does not exist in the actuals dataframe"

        df_result = pd.DataFrame(columns=['measurement', 'region_id', 'timestamp', 'value', 'extra_data'])

        # Calculate estimates
        if region_id:
            if self.verbose > 0:
                print('\n##### Calculating for region:', region_id, '#####')
            results = [self.get_region_estimation(measurement, region_id, timestamp, ignore_site_ids)]
        else:
            if self.verbose > 1:
                print('No region_id submitted so calculating for all region ids...')
            results = []
            for index, _ in self.regions.iterrows():
                if self.verbose > 0:
                    print('Calculating for region:', index)
                results.append(self.get_region_estimation(measurement, index, timestamp, ignore_site_ids))

        for item in results:
            for estimate in item['estimates']:
                df_result = df_result.append({  'measurement': measurement,
                                                'region_id': item['region_id'],
                                                'timestamp': estimate['timestamp'],
                                                'value': estimate['value'],
                                                'extra_data': json.dumps(estimate['extra_data'])
                                                }
                                             , ignore_index=True)

        return df_result


    def get_region_estimation(self, measurement, region_id, timestamp=None, ignore_site_ids=[]):
        """  Find estimations for a region and timestamp (or all timestamps (or all timestamps if timestamp==None)

            :param measurement: measurement to be estimated (string, required)
            :param region_id: region identifier (string, required)
            :param timestamp:  timestamp identifier (string or None)
            :param ignore_site_ids: site id(s) to be ignored during the estimations

            :return: a dict with items 'region_id' and 'estimates (list). Estimates contains
                        'timestamp', (estimated) 'value' and 'extra_data'
        """
        region_result = {'region_id': region_id, 'estimates': []}

        if timestamp is not None:
            if self.verbose > 0:
                print('\n##### Calculating for region_id: {} and timestamp: {} #####'.format(region_id, timestamp))

            region_result_estimate = self.get_estimate(measurement, timestamp, region_id, ignore_site_ids)

            if self.verbose > 0:
                print(region_id, '    Calculated for timestamp:', region_result_estimate)

            region_result['estimates'].append({'value': region_result_estimate[0],
                                               'extra_data': region_result_estimate[1],
                                               'timestamp': timestamp})
        else:
            timestamps = sorted(self.actuals['timestamp'].unique())
            for _, timestamp in enumerate(timestamps):
                if self.verbose > 0:
                    print(region_id, '    Calculating for timestamp:', timestamp)

                region_result_estimate = self.get_estimate(measurement, timestamp, region_id, ignore_site_ids)

                if self.verbose > 0:
                    print(region_id, '    Calculated for ', timestamp, ':', region_result_estimate)

                region_result['estimates'].append({'value':region_result_estimate[0],
                                                   'extra_data': region_result_estimate[1],
                                                   'timestamp': timestamp}
                                                  )
        return region_result


    def get_adjacent_regions(self, region_ids, ignore_regions=[]):
        """  Find all adjacent regions for list a of region ids
             Uses the neighbouring regions found in set-up, using __get_all_region_neighbours

            :param region_ids: list of region identifier (list of strings)
            :param ignore_regions:  list of region identifier (list of strings): list to be ignored

            :return: a list of regions_ids (empty list if no adjacent regions)
        """

        if self.verbose > 0:
            print('\ngetting adjacent regions...')

        # Create an empty list for adjacent regions
        adjacent_regions = []
        # Get all adjacent regions for each region
        df_reset = self.regions.reset_index()
        for region_id in region_ids:
            if self.verbose > 1:
                print('getting adjacent regions for {}'.format(region_id))
            regions_temp = df_reset.loc[df_reset['region_id'] == region_id]
            if len(regions_temp.index) > 0:
                adjacent_regions.extend(regions_temp['neighbours'].iloc[0].split(','))

        # Return all adjacent regions as a querySet and remove any that are in the completed/ignore list.
        return [x for x in adjacent_regions if x not in ignore_regions and x.strip() != '']

    def site_datapoint_count(self, measurement, timestamp, region_ids=[], ignore_site_ids=[]):
        '''
        Find the number of site datapoints for this measurement, timestamp and (optional) regions combination

        :param measurement: (str) the measurement being recorded in the site data-point
        :param timestamp: (timestamp) the timestamp of the site datapoints being searched for
        :param region_ids: (list of str) list of region IDs
        :param ignore_site_ids list of site_ids to be ignored

        :return: Number of sites
        '''
        sites = self.actuals.loc[(self.actuals['timestamp'] == timestamp) & (self.actuals[measurement].notna())
                                   & (~self.actuals['site_id'].isin(ignore_site_ids))]
        sites = sites['site_id'].tolist()

        region_sites = []
        for region_id in region_ids:
            region_sites.extend(self.regions.loc[region_id]['sites'])

        if len(region_ids) > 0:
            return len(set(sites) & set(region_sites))
        else:
            return len(set(sites))

    def get_region_sites(self, region_id):
        '''
            Find all sites within the region identified by region_id
            as comma-delimited string of site ids.

            :param region_id:  (str) a region id (must be (an index) in self.regions)

            :return: A list of site IDs (list of str)
        '''
        assert region_id in self.regions.index.tolist(), 'region_id is not in list of regions'
        result = self.regions.loc[[region_id]]['sites'][0].strip().split(',')
        return list(filter(self.is_valid_site_id, result))

    def get_regions_sites(self, region_ids, ignore_site_ids=[]):
        '''
        Retrieve the number of sites (in self.sites) for the list of region_ids

        :param region_ids: (list of str) list of region IDs
        :param ignore_site_ids: (list of str) list of site_ids to be ignored

        :return: list of site IDs
        '''
        # Create an empty queryset for sites found in regions
        sites = []

        if self.verbose > 0:
            print('Finding sites in region_ids: {}'.format(region_ids))

        # Find sites in region_ids
        for region_id in region_ids:
            if self.verbose > 1:
                print('Finding sites in region {}'.format(region_id))
            sites.extend(self.get_region_sites(region_id))
        return list(set(sites) - set(ignore_site_ids))

    def get_region_id(self, site_id):
        '''
            Retrieve the region_id that the site with site_id is in

            :param site_id: (str) site ID

            :return: (str) the region ID held in the 'region_id' column for the site object
        '''
        assert self.is_valid_site_id(site_id), 'Invalid site ID'
        assert site_id in self.sites.index.tolist(), 'site_id not in list of available sites'

        return self.sites.loc[[site_id]]['region_id'][0]


    def __get_region_sites(self, region):
        return self.sites[self.sites.geometry.within(region['geometry'])].index.tolist()

    def __set_region_sites(self):
        '''
            Find all of the sites within each region and add to a 'sites' column in self.regions -
            as comma-delimited string of site ids.

            :return: No return value
        '''
        if self.verbose > 0:
            print('\ngetting all region sites...')

        for index, region in self.regions.iterrows():
            sites = self.__get_region_sites(region)
            sites_str = ",".join(str(x) for x in sites)
            self.regions.at[index, "sites"] = sites_str

            if self.verbose > 1:
                print('region {}: {}'.format(index, sites_str))

    def __set_site_region(self):
        '''
            Find all of the region ids for each site and add to a 'region_id' column in self.sites
            Adds None if not found.

            :return: No return value
        '''
        if self.verbose > 0:
            print('\ngetting region for each site...')

        # Create new column with empty string as values
        self.sites["region_id"] = ""

        for index, region in self.regions.iterrows():
            self.sites = self.sites.assign(
                **{'region_id': np.where(self.sites.within(region.geometry), index, self.sites['region_id'])}
            )
