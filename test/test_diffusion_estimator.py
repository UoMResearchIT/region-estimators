import unittest
from os import path
from shapely import wkt
import pandas as pd
import numpy as np

from region_estimators.diffusion_estimator import DiffusionEstimator

class TestRegionEdgeCases(unittest.TestCase):
  """
  Tests for the Regions file edge cases
  """

  def setUp(self):
    dir, _ = path.split(__file__)
    self.load_data_path = path.join(dir, 'data', 'OK')

    self.sensors = pd.read_csv(
      path.join(self.load_data_path, 'sensors.csv'),
      index_col='sensor_id'
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
      path.join(self.load_data_path, 'results_diffusion.csv')
    )
    self.results_ignore_sensors = pd.read_csv(
      path.join(self.load_data_path, 'results_diffusion_ignore_sensors.csv')
    )


  def test_ok_files(self):
    """
    Test that a DiffusionEstimator object can be initialized with region data containing regions that are all touching
    and that the results are as expected
    """
    estimator = DiffusionEstimator(self.sensors, self.regions, self.actuals,
                                            verbose=0)

    self.assertEqual(estimator.get_adjacent_regions(['SW']), ['CR', 'KT', 'SE', 'SM', 'TW', 'W', 'WC'])
    result = estimator.get_estimations('NO2_mean', None, '2019-10-15')

    #print('Result: \n {}'.format(result))
    #print('Target: \n {}'.format(self.results_touching))

    self.assertIsNotNone(estimator)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, pd.DataFrame)
    self.assertTrue(result.equals(self.results))

  def test_ignore_sensors(self):
    """
    Test that a DiffusionEstimator object can be initialized with region data containing regions that are all touching
    and that the results are as expected when ignoring sensors
    """
    estimator = DiffusionEstimator(self.sensors, self.regions, self.actuals, verbose=0)
    result = estimator.get_estimations('NO2_mean', None, '2019-10-15', ignore_sensor_ids=['Camden Kerbside [AQ]'])

    #print('Result: \n {}'.format(result))
    #print('Target: \n {}'.format(self.results_ignore_sensors))

    self.assertIsNotNone(estimator)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, pd.DataFrame)
    self.assertTrue(result.equals(self.results_ignore_sensors))
