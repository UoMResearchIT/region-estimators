import unittest
from os import path
from shapely import wkt
import pandas as pd
import numpy as np

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
    self.load_data_path = path.join(dir, 'data', 'edge_cases')

    self.sensors_islands = pd.read_csv(
      path.join(self.load_data_path, 'sensors_islands.csv'),
      index_col='sensor_id'
    )

    self.sensors_non_touching = pd.read_csv(
      path.join(self.load_data_path, 'sensors_non_touching.csv'),
      index_col='sensor_id'
    )

    self.sensors_overlap = pd.read_csv(
      path.join(self.load_data_path, 'sensors_overlap.csv'),
      index_col='sensor_id'
    )

    self.actuals_islands = pd.read_csv(
      path.join(self.load_data_path, 'actuals_islands.csv')
    )

    self.actuals_non_touching = pd.read_csv(
      path.join(self.load_data_path, 'actuals_non_touching.csv')
    )

    self.actuals_overlap = pd.read_csv(
      path.join(self.load_data_path, 'actuals_overlap.csv')
    )

    self.regions_islands = pd.read_csv(
      path.join(self.load_data_path, 'regions_islands.csv'),
      index_col='region_id'
    )
    self.regions_islands['geometry'] = self.regions_islands.apply(
      lambda row: wkt.loads(row.geometry),
      axis=1
    )

    self.regions_non_touching = pd.read_csv(
      path.join(self.load_data_path, 'regions_non_touching.csv'),
      index_col='region_id'
    )
    self.regions_non_touching['geometry'] = self.regions_non_touching.apply(
      lambda row: wkt.loads(row.geometry),
      axis=1
    )

    self.regions_overlap = pd.read_csv(
      path.join(self.load_data_path, 'regions_overlap.csv'),
      index_col='region_id'
    )
    self.regions_overlap['geometry'] = self.regions_overlap.apply(
      lambda row: wkt.loads(row.geometry),
      axis=1
    )

    self.results_islands = pd.read_csv(
      path.join(self.load_data_path, 'results_islands_distance.csv')
    )
    self.results_non_touching = pd.read_csv(
      path.join(self.load_data_path, 'results_non_touching_distance.csv')
    )
    self.results_overlap = pd.read_csv(
      path.join(self.load_data_path, 'results_overlap_distance.csv'),
      doublequote=True,
      converters={'extra_data': self.CustomJSONParser}
    )



  def test_islands(self):
    """
    Test that a DistanceEstimator object can be initialized with region data containing islands
    and that the results are as expected for islands
    """
    estimator_islands = DistanceSimpleEstimator(self.sensors_islands, self.regions_islands, self.actuals_islands,
                                           verbose=0)
    result = estimator_islands.get_estimations('NO2_mean', None, '2019-10-15')
    #print('Islands results: \n {}'.format(result))
    #print('Islands target: \n {}'.format(self.results_islands))

    self.assertIsNotNone(estimator_islands)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, pd.DataFrame)
    self.assertTrue(result.equals(self.results_islands))

  def test_non_touching(self):
    """
    Test that a DistanceEstimator object can be initialized with region data containing regions that are
    not  touching and that the results are as expected
    """
    estimator_non_touching = DistanceSimpleEstimator(self.sensors_non_touching, self.regions_non_touching,
                                                self.actuals_non_touching, verbose=0)
    result = estimator_non_touching.get_estimations('NO2_mean', None, '2019-10-15')

    #print('Non Touching: \n {}'.format(result))
    #print('Non Touching target: \n {}'.format(self.results_non_touching))

    self.assertIsNotNone(estimator_non_touching)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, pd.DataFrame)
    self.assertTrue(result.equals(self.results_non_touching))

  def test_overlapping(self):
    """
    Test that a DistanceEstimator object can be initialized with region data containing regions that are overlapping
    and that the results are as expected
    """
    estimator_overlap = DistanceSimpleEstimator(self.sensors_overlap, self.regions_overlap, self.actuals_overlap,
                                           verbose=0)
    result = estimator_overlap.get_estimations('NO2_mean', None, '2019-10-15')

    #print('Overlap: \n {}'.format(result))
    #print('Overlap target: \n {}'.format(self.results_overlap))
    #print('Difference:\n{}'.format(result.compare(self.results_overlap)))

    self.assertIsNotNone(estimator_overlap)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, pd.DataFrame)
    self.assertTrue(result.equals(self.results_overlap))
