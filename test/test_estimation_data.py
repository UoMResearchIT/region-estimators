import unittest
from os import path
from shapely import wkt
import pandas as pd

from region_estimators.region_estimator import RegionEstimator
from region_estimators.concentric_regions_estimator import ConcentricRegionsEstimator
from region_estimators.distance_simple_estimator import DistanceSimpleEstimator
from region_estimators.estimation_data import EstimationData

class TestEstimationData(unittest.TestCase):
  """
  Tests for the EstimationData class.
  """

  def setUp(self):
    dir, _ = path.split(__file__)
    self.load_data = path.join(dir, 'data', 'loading')

    self.sites = pd.read_csv(
      path.join(self.load_data, 'sites.csv'),
      index_col='site_id'
    )
    self.regions = pd.read_csv(
      path.join(self.load_data, 'regions.csv'),
      index_col='region_id'
    )
    self.regions['geometry'] = self.regions.apply(
      lambda row: wkt.loads(row.geometry),
      axis=1
    )

    self.actuals = pd.read_csv(path.join(self.load_data, 'actuals_multi_measurements.csv'))

  def test_site_datapoint_count(self):
    """
    Test that a RegionEstimator object can be initialized with good data.
    Also check that various other initializations happen within the object.
    """
    estimation_data = EstimationData(self.sites, self.regions, self.actuals)

    self.assertEqual(estimation_data.site_datapoint_count('urtica', '2018-03-14', ignore_site_ids=None), 2)
    self.assertEqual(estimation_data.site_datapoint_count('urtica', '3318-03-14', ignore_site_ids=None), 0)
