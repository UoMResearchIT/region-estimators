import unittest
from os import path
from shapely import wkt
import pandas as pd

from region_estimators.region_estimator import RegionEstimator

class TestRegionEstimator(unittest.TestCase):
  """
  Tests for the RegionEstimator abstract base class.
  """

  def setUp(self):
    dir, _ = path.split(__file__)
    self.load_data = path.join(dir, 'data', 'loading')

    self.sensors = pd.read_csv(
      path.join(self.load_data, 'sensors.csv'),
      index_col='sensor_id'
    )

    self.regions = pd.read_csv(
      path.join(self.load_data, 'regions.csv'),
      index_col='region_id'
    )
    self.regions['geometry'] = self.regions.apply(
      lambda row: wkt.loads(row.geometry),
      axis=1
    )

    self.actuals = pd.read_csv(path.join(self.load_data, 'actuals.csv'))

  def test_load_good_data(self):
    """
    Test that a RegionEstimator object can be initialized with good data.
    Also check that various other initializations happen within the object.
    """
    estimator = RegionEstimator(self.sensors, self.regions, self.actuals)

    self.assertIsNotNone(estimator)
    self.assertIsNotNone(estimator.regions['neighbours'])
    self.assertIsNotNone(estimator.regions['sensors'])

    self.assertTrue(estimator.sensors_exist('urtica', '2018-03-15'))

    self.assertEqual(estimator.get_adjacent_regions(['BL'], []), ['BB'])

    with self.assertRaises(NotImplementedError):
      estimator.get_estimate('urtica', None, None)
