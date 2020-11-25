import unittest
from os import path
from shapely import wkt
import pandas as pd

from region_estimators.region_estimator import RegionEstimator
from region_estimators.diffusion_estimator import DiffusionEstimator
from region_estimators.distance_simple_estimator import DistanceSimpleEstimator

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

    self.assertTrue(estimator.sensor_datapoint_count('urtica', '2018-03-15') > 0)

    self.assertEqual(estimator.get_adjacent_regions(['BL'], []), ['BB'])

    with self.assertRaises(NotImplementedError):
      estimator.get_estimate('urtica', None, None)

  def test_load_bad_verbose(self):
    """
    Test that a DiffusionEstimator and DistanceSimpleEstimator objects can
    be initialized with bad verbose.
    """
    with self.assertRaises(AssertionError):
      DiffusionEstimator(self.sensors, self.regions, self.actuals, 'bad')

    with self.assertRaises(AssertionError):
      DistanceSimpleEstimator(self.sensors, self.regions, self.actuals, 2.14)


  def test_load_actuals_with_bad_data(self):
    """
    Check that loading bad actuals data will fail.
    """
    bad_files = [
      'actuals_no_id.csv',
      'actuals_no_timestamp.csv',
      'actuals_no_measurements.csv'
    ]

    for file in bad_files:
      with self.subTest(file=file):
        with self.assertRaises(AssertionError):
          bad_actuals = pd.read_csv(path.join(self.load_data, file))
          DiffusionEstimator(self.sensors, self.regions, bad_actuals)

  def test_load_regions_with_bad_data(self):
    """
    Check that loading bad regions data will fail.
    """
    bad_files = [
      'regions_no_geometry.csv'
    ]

    for file in bad_files:
      with self.subTest(file=file):
        with self.assertRaises(AssertionError):
          bad_regions = pd.read_csv(path.join(self.load_data, file))
          DiffusionEstimator(self.sensors, bad_regions, self.actuals)

  def test_load_sensors_with_bad_data(self):
    """
    Check that loading bad sensor data will fail.
    """
    bad_files = [
      'sensors_no_latitude.csv',
      'sensors_no_longitude.csv',
      'sensors_bad_latitude.csv',
      'sensors_bad_longitude.csv'
    ]

    for file in bad_files:
      with self.subTest(file=file):
        with self.assertRaises(AssertionError):
          bad_sensors = pd.read_csv(path.join(self.load_data, file))
          DistanceSimpleEstimator(bad_sensors, self.regions, self.actuals)
