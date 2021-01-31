import unittest
from os import path
from shapely import wkt
import pandas as pd
from region_estimators.estimation_data import EstimationData

from region_estimators.distance_simple_estimator import DistanceSimpleEstimator

class TestRegionEdgeCases(unittest.TestCase):
  """
  Tests for the Regions file edge cases
  """

  def CustomJSONParser(self, data):
    import json
    j1 = json.dumps(json.loads(data))
    return j1

  def setUp(self):
    dir, _ = path.split(__file__)
    self.load_data_path = path.join(dir, 'data', 'OK')

    self.sites = pd.read_csv(
      path.join(self.load_data_path, 'sites.csv'),
      index_col='site_id'
    )

    self.actuals = pd.read_csv(
      path.join(self.load_data_path, 'actuals.csv')
    )

    self.regions = pd.read_csv(
      path.join(self.load_data_path, 'regions.csv'),
      index_col='region_id'
    )
    self.regions['geometry'] = self.regions.apply(
      lambda row: wkt.loads(row.geometry),
      axis=1
    )

    self.results = pd.read_csv(
      path.join(self.load_data_path, 'results_distance.csv'),
      index_col=['measurement', 'region_id', 'timestamp']
    )
    self.results_ignore_sites = pd.read_csv(
      path.join(self.load_data_path, 'results_distance_ignore_sites.csv'),
      index_col=['measurement', 'region_id', 'timestamp']
    )

  def test_ok_files(self):
    """
    Test that a DistanceEstimator object can be initialized with region data containing regions that are all touching
    and that the results are as expected
    """
    estimation_data = EstimationData(self.sites, self.regions, self.actuals)
    estimator = DistanceSimpleEstimator(estimation_data, verbose=0)
    result = estimator.get_estimations('NO2_mean', None, '2019-10-15')

    #print('Result: \n {}'.format(result))
    #print('Target: \n {}'.format(self.results_touching))

    self.assertIsNotNone(estimator)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, pd.DataFrame)
    self.assertTrue(result.equals(self.results))

  def test_ignore_sites(self):
    """
    Test that a DiffusionEstimator object can be initialized with region data containing regions that all touching
    and that the results are as expected when ignoring sites
    """
    estimation_data = EstimationData(self.sites, self.regions, self.actuals)
    estimator = DistanceSimpleEstimator(estimation_data, verbose=0)
    result = estimator.get_estimations('NO2_mean', None, '2019-10-15', ignore_site_ids=['Camden Kerbside [AQ]'])

    #print('Result: \n {}'.format(result))
    #print('Target: \n {}'.format(self.results_ignore_sites))

    self.assertIsNotNone(estimator)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, pd.DataFrame)
    self.assertTrue(result.equals(self.results_ignore_sites))