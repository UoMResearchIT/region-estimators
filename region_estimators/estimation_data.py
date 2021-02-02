import geopandas as gpd
import pandas as pd
import numpy as np
import multiprocessing

class EstimationData(object):
    VERBOSE_DEFAULT = 0
    VERBOSE_MAX = 2

    def __init__(self, sites, regions, actuals, verbose=0):
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

         Returns:
             Initialised instance of subclass of RegionEstimator

         """
        ### Check and set verbose
        self.verbose = verbose

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
                # df_temp = actuals.loc[actuals[column].notnull()]
                try:
                    pd.to_numeric(actuals[column], errors='raise').notnull()  # .all()
                except:
                    raise AssertionError(
                        "actuals['" + column + "'] column contains non-numeric values (null values are accepted).")

        # Check that each site_id value is present in the sites dataframe index.
        # ... So site_id values must be a subset of allowed sites
        error_sites = set(actuals['site_id'].unique()) - set(sites.index.values)
        assert len(error_sites) == 0, \
            "Each site ID must match a site_id in sites. Error site IDs: " + str(error_sites)

        # Convert to geo dataframe
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

        # actuals: Make sure value columns at the end of column list
        cols = actuals.columns.tolist()
        cols.insert(0, cols.pop(cols.index('site_id')))
        cols.insert(0, cols.pop(cols.index('timestamp')))
        actuals = actuals[cols]
        # Convert site_id to string
        actuals['site_id'] = actuals['site_id'].astype(str)

        # Set data properties
        self._sites = gdf_sites
        self._regions = gdf_regions
        self._actuals = actuals

        # Set extra useful data for estimation calculations
        self.__set_site_region()
        self.__set_region_sites()

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, verbose=VERBOSE_DEFAULT):
        assert isinstance(verbose, int), \
            "Verbose level must be an integer not {}. (zero or less produces no debug output)".format(verbose.__class__)
        if verbose < 0:
            print('Warning: verbose input is less than zero so setting to zero')
            verbose = 0
        if verbose > EstimationData.VERBOSE_MAX:
            print('Warning: verbose input is greater than {}} so setting to {}'.format(
                EstimationData.VERBOSE_MAX, EstimationData.VERBOSE_MAX))
            verbose = EstimationData.VERBOSE_MAX
        self._verbose = verbose

    @property
    def sites(self):
        return self._sites

    @property
    def regions(self):
        return self._regions

    @property
    def actuals(self):
        return self._actuals

    @staticmethod
    def is_valid_site_id(site_id):
        '''
            Check if site ID is valid (non empty string)

            :param site_id:  (str) a site id

            :return: True if valid, False otherwise
        '''
        return site_id is not None and isinstance(site_id, str) and len(site_id) > 0


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
        Retrieve the number of sites (in self._sites) for the list of region_ids

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
        assert site_id in self._sites.index.tolist(), 'site_id not in list of available sites'

        return self._sites.loc[[site_id]]['region_id'][0]


    def __get_region_sites(self, region):
        return self._sites[self._sites.geometry.within(region['geometry'])].index.tolist()

    def __set_region_sites(self):
        '''
            Find all of the sites within each region and add to a 'sites' column in self.regions -
            as comma-delimited string of site ids.

            :return: No return value
        '''
        if self.verbose > 0:
            print('\ngetting all sites for each region...')

        for index, region in self.regions.iterrows():
            sites = self.__get_region_sites(region)
            sites_str = ",".join(str(x) for x in sites)
            self.regions.at[index, "sites"] = sites_str

            if self.verbose > 1:
                print('set sites for region {}: {}'.format(index, sites_str))

    def __set_site_region(self):
        '''
            Find all of the region ids for each site and add to a 'region_id' column in self._sites
            Adds None if not found.

            :return: No return value
        '''
        if self.verbose > 0:
            print('\ngetting region for each site...')

        # Create new column with empty string as values
        self._sites["region_id"] = ""

        for index, region in self.regions.iterrows():
            self._sites = self._sites.assign(
                **{'region_id': np.where(self._sites.within(region.geometry), index, self._sites['region_id'])}
            )

        if self.verbose > 0:
            print('regions: \n {}'.format(self._sites['region_id']))

    def site_datapoint_count(self, measurement, timestamp, region_ids=[], ignore_site_ids=[]):
        '''
        Find the number of site datapoints for this measurement, timestamp and (optional) regions combination

        :param measurement: (str) the measurement being recorded in the site data-point
        :param timestamp: (timestamp) the timestamp of the site datapoints being searched for
        :param region_ids: (list of str) list of region IDs
        :param ignore_site_ids list of site_ids to be ignored

        :return: Number of sites
        '''

        if ignore_site_ids is None:
            ignore_site_ids = []

        sites = self.actuals.loc[(self.actuals['timestamp'] == timestamp) &
                                 (self.actuals[measurement].notna()) &
                                 (~self.actuals['site_id'].isin(ignore_site_ids))]

        if sites is None or len(sites.index) == 0:
            return 0

        sites = sites['site_id'].tolist()

        region_sites = []
        for region_id in region_ids:
            region_sites.extend(self.regions.loc[region_id]['sites'])

        if len(region_ids) > 0:
            return len(set(sites) & set(region_sites))
        else:
            return len(set(sites))
