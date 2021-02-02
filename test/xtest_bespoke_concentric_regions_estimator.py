import unittest
from os import path
from shapely import wkt
import pandas as pd

from region_estimators.estimation_data import EstimationData
from region_estimators.concentric_regions_estimator import ConcentricRegionsEstimator

class TestRegionEdgeCasesBespoke(unittest.TestCase):
  """
  Tests for the Regions file edge cases
  """

  def setUp(self):
    dir, _ = path.split(__file__)
    self.load_data_path = path.join(dir, 'data', 'BESPOKE')

    self.sites = pd.read_csv(
      path.join(self.load_data_path, 'sites_DEBUG.csv'),
      index_col='site_id'
    )

    self.actuals = pd.read_csv(
      path.join(self.load_data_path, 'actuals_DEBUG.csv')
    )

    self.regions = pd.read_csv(
      path.join(self.load_data_path, 'regions_DEBUG.csv'),
      index_col='region_id'
    )
    self.regions['geometry'] = self.regions.apply(
      lambda row: wkt.loads(row.geometry),
      axis=1
    )

  def test_bespoke(self):
    """
    Test a bespoke set of files
    """
    estimation_data = EstimationData(self.sites, self.regions, self.actuals)
    estimator = ConcentricRegionsEstimator(estimation_data, verbose=0, max_processors=4)

    self.assertIsNotNone(estimator.regions['neighbours'])
    self.assertEqual(estimator.estimation_data.get_adjacent_regions(['SW']), ['CR', 'KT', 'SE', 'SM', 'TW', 'W', 'WC'])
    result = estimator.get_estimations('NO2_mean', None, '2016-03-23')

    print('Sites:\n{}'.format(estimator.sites))
    print('Regions:\n{}'.format(estimator.regions))
    print('Actuals:\n{}'.format(estimator.actuals))
    print('Result: \n {}'.format(result))

    self.assertIsNotNone(estimator)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, pd.DataFrame)
