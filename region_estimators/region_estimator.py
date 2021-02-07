from abc import ABCMeta, abstractmethod
import pandas as pd
import numpy as np
import multiprocessing
import json
import time

from region_estimators.estimation_data import EstimationData

def log_time(func):
    """Logs the time it took for func to execute"""

    def wrapper(*args, **kwargs):
        start = time.time()
        val = func(*args, **kwargs)
        end = time.time()
        duration = end - start
        print(f'{func.__name__} took {duration} seconds to run')
        return val

    return wrapper

class RegionEstimator(object):
    """
        Abstract class, parent of region estimators (each implementing a different estimation method).
        Requires GeoPandas and Pandas
    """
    __metaclass__ = ABCMeta

    VERBOSE_DEFAULT = 0
    VERBOSE_MAX = 2
    MAX_NUM_PROCESSORS = 1

    @log_time
    def __init__(self, estimation_data=None, verbose=VERBOSE_DEFAULT, max_processors=MAX_NUM_PROCESSORS):
        """
        Initialise instance of the RegionEstimator class.

        Args:
            estimation_data: (EstimationData) The data to be used in the estimations

            verbose: (int) Verbosity of output level. zero or less => No debug output

            max_processors: (int) The maximum number of processors to be used when calculating regions.

        Returns:
            Initialised instance of subclass of RegionEstimator

        """

        # Check and set verbose
        self.verbose = verbose

        # Check and set max_processors
        # On local machine, multiprocessing.cpu_count() == 4
        self.max_processors = min(max_processors, multiprocessing.cpu_count())

        # Set EstimationData
        self._estimation_data = estimation_data

    @abstractmethod
    def get_estimate(self, measurement, timestamp, region_id, ignore_site_ids=[]):
        raise NotImplementedError("Must override get_estimate")

    @property
    def estimation_data(self):
        return self._estimation_data

    @estimation_data.setter
    def estimation_data(self, estimation_data):
        assert estimation_data is None or isinstance(estimation_data, EstimationData), \
            "estimation_data must be an instance of type EstimationData"
        self._estimation_data = estimation_data

    @property
    def sites(self):
        return self._estimation_data.sites

    @property
    def regions(self):
        return self._estimation_data.regions

    @property
    def actuals(self):
        return self._estimation_data.actuals

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
        if verbose > RegionEstimator.VERBOSE_MAX:
            print('Warning: verbose input is greater than {}} so setting to {}'.format(
                RegionEstimator.VERBOSE_MAX, RegionEstimator.VERBOSE_MAX))
            verbose = RegionEstimator.VERBOSE_MAX
        self._verbose = verbose

    @property
    def max_processors(self):
        return self.__max_processors

    @max_processors.setter
    def max_processors(self, max_processors=MAX_NUM_PROCESSORS):
        assert isinstance(max_processors, int), "max_processors must be an integer."
        assert max_processors > 0, "max_processors must be greater than zero"
        self.__max_processors = max_processors

    def _get_estimate_process(self, region_result, measurement, region_id, timestamp, ignore_site_ids=[]):
        """  Find estimation for a single region and single timestamp. Worker function for multi-processing.

            :region_result: estimation result. as multiprocessing is used must return result as parameter
            :param measurement: measurement to be estimated (string, required)
            :param region_id: region identifier (string, required)
            :param timestamp:  timestamp identifier (string, required)
            :param ignore_site_ids: site id(s) to be ignored during the estimations. Default=[]

            :return: a dict with items 'region_id' and 'estimates (list). Estimates contains
                        'timestamp', (estimated) 'value' and 'extra_data'
        """
        try:
            region_result_estimate = self.get_estimate(measurement, timestamp, region_id, ignore_site_ids)
            region_result.append({'measurement': measurement,
                                  'region_id': region_id,
                                  'value': region_result_estimate[0],
                                  'extra_data': json.dumps(region_result_estimate[1]),
                                  'timestamp': timestamp})
        except Exception as err:
            print('Error estimating for measurement: {}; region: {}; timestamp: {} and ignore_sites: {}.\nError: {}'
                  .format(measurement, region_id, timestamp, ignore_site_ids, err))

    def _get_region_estimation(self, pool, region_result, measurement, region_id, timestamp=None, ignore_site_ids=[]):
        """  Find estimations for a region and timestamp (or all timestamps (or all timestamps if timestamp==None)

            :param pool: the multiprocessing pool object within which to run this task
            :region_result: estimation result. as multiprocessing is used must return result as parameter
            :param measurement: measurement to be estimated (string, required)
            :param region_id: region identifier (string, required)
            :param timestamp:  timestamp identifier (string or None)
            :param ignore_site_ids: site id(s) to be ignored during the estimations

            :return: a dict with items 'region_id' and 'estimates (list). Estimates contains
                        'timestamp', (estimated) 'value' and 'extra_data'
        """

        if timestamp is not None:
            if self.verbose > 0:
                print('\n##### Calculating for region_id: {} and timestamp: {} #####'.format(region_id, timestamp))
            pool.apply_async(self._get_estimate_process,
                                 args=(region_result, measurement, region_id, timestamp, ignore_site_ids))
        else:
            timestamps = sorted(self.actuals['timestamp'].unique())
            for _, timestamp in enumerate(timestamps):
                if self.verbose > 1:
                    print(region_id, '    Calculating for timestamp:', timestamp)
                pool.apply_async(self._get_estimate_process,
                                     args=(region_result, measurement, region_id, timestamp, ignore_site_ids))
        return region_result

    @log_time
    def get_estimations(self, measurement, region_id=None, timestamp=None, ignore_site_ids=[]):
        """  Find estimations for a region (or all regions if region_id==None) and
                timestamp (or all timestamps (or all timestamps if timestamp==None)

            :param measurement: measurement to be estimated (string - required)
            :param region_id: region identifier (string or None)
            :param timestamp:  timestamp identifier (string or None)
            :param ignore_site_ids: site id(s) to be ignored during the estimations (default: empty list [])

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

        if ignore_site_ids is None:
            ignore_site_ids = []

        # Calculate estimates

        with multiprocessing.Manager() as manager, multiprocessing.Pool(self.max_processors) as pool:
            # Set up pool and result dict
            region_result = manager.list()

            if region_id:
                if self.verbose > 0:
                    print('\n##### Calculating for region:', region_id, '#####')
                self._get_region_estimation(pool, region_result, measurement, region_id, timestamp, ignore_site_ids)
            else:
                if self.verbose > 0:
                    print('No region_id submitted so calculating for all region ids...')
                for index, _ in self.regions.iterrows():
                    if self.verbose > 1:
                        print('Calculating for region:', index)
                    self._get_region_estimation(pool, region_result, measurement, index, timestamp, ignore_site_ids)

            pool.close()
            pool.join()

            # Put results into the results dataframe
            df_result = pd.DataFrame.from_records(region_result)
            if len(df_result.index) > 0:
                df_result.set_index(['measurement', 'region_id', 'timestamp'], inplace=True)
            else:
                raise ValueError("Estimation process returned no results.")

        return df_result
