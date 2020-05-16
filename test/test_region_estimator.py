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

  def test_load_actuals_with_no_id(self):
    """
    Check that loading actuals data without a sensor_id column will fail.
    """
    bad_actuals = pd.read_csv(path.join(self.load_data, 'actuals_no_id.csv'))

    with self.assertRaises(AssertionError):
      RegionEstimator(self.sensors, self.regions, bad_actuals)

  def test_load_actuals_with_no_timestamp(self):
    """
    Check that loading actuals data without a timestamp column will fail.
    """
    bad_actuals = pd.read_csv(
      path.join(self.load_data, 'actuals_no_timestamp.csv')
    )

    with self.assertRaises(AssertionError):
      RegionEstimator(self.sensors, self.regions, bad_actuals)

  def test_load_actuals_with_no_measurements(self):
    """
    Check that loading actuals data without any measurements will fail.
    """
    bad_actuals = pd.read_csv(
      path.join(self.load_data, 'actuals_no_measurements.csv')
    )

    with self.assertRaises(AssertionError):
      RegionEstimator(self.sensors, self.regions, bad_actuals)

  def test_load_regions_with_no_geometry(self):
    """
    Check that loading regions without any geometry will fail.
    """
    bad_regions = pd.read_csv(
      path.join(self.load_data, 'regions_no_geometry.csv')
    )

    with self.assertRaises(AssertionError):
      RegionEstimator(self.sensors, bad_regions, self.actuals)