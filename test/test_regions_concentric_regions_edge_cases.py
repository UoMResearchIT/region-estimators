import unittest
from os import path
from shapely import wkt
import pandas as pd
import numpy as np

from region_estimators.concentric_regions_estimator import ConcentricRegionsEstimator
from region_estimators.estimation_data import EstimationData

class TestRegionEdgeCases(unittest.TestCase):
  """
  Tests for the Regions file edge cases
  """

  def setUp(self):
    dir, _ = path.split(__file__)
    self.load_data_path = path.join(dir, 'data', 'edge_cases')

    self.sites_islands = pd.read_csv(
      path.join(self.load_data_path, 'sites_islands.csv'),
      index_col='site_id'
    )

    self.sites_non_touching = pd.read_csv(
      path.join(self.load_data_path, 'sites_non_touching.csv'),
      index_col='site_id'
    )

    self.sites_overlap = pd.read_csv(
      path.join(self.load_data_path, 'sites_overlap.csv'),
      index_col='site_id'
    )

    self.sites_empty_measurements = pd.read_csv(
      path.join(self.load_data_path, 'sites_empty_measurements.csv'),
      index_col='site_id'
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

    self.actuals_empty_measurements = pd.read_csv(
      path.join(self.load_data_path, 'actuals_empty_measurements.csv')
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

    self.regions_empty_measurements = pd.read_csv(
      path.join(self.load_data_path, 'regions_empty_measurements.csv'),
      index_col='region_id'
    )
    self.regions_empty_measurements['geometry'] = self.regions_empty_measurements.apply(
      lambda row: wkt.loads(row.geometry),
      axis=1
    )

    self.results_islands = pd.read_csv(
      path.join(self.load_data_path, 'results_islands_concentric_regions.csv'),
      index_col=['measurement', 'region_id', 'timestamp']
    )
    self.results_non_touching = pd.read_csv(
      path.join(self.load_data_path, 'results_non_touching_concentric_regions.csv'),
      index_col=['measurement', 'region_id', 'timestamp']
    )
    self.results_overlap = pd.read_csv(
      path.join(self.load_data_path, 'results_overlap_concentric_regions.csv'),
      index_col=['measurement', 'region_id', 'timestamp']
    )
    self.results_empty_measurements = pd.read_csv(
      path.join(self.load_data_path, 'results_empty_measurements.csv'),
      index_col=['measurement', 'region_id', 'timestamp']
    )


  def test_islands(self):
    """
    Test that a ConcentricRegionsEstimator object can be initialized with region data containing islands
    and that the results are as expected for islands
    """
    estimation_data = EstimationData(self.sites_islands, self.regions_islands, self.actuals_islands)
    estimator_islands = ConcentricRegionsEstimator(estimation_data, verbose=0)
    self.assertEqual(estimator_islands.estimation_data.get_adjacent_regions(['IM']), [])
    self.assertEqual(estimator_islands.estimation_data.get_adjacent_regions(['BT']), [])
    result = estimator_islands.get_estimations('NO2_mean', None, '2019-10-15').fillna(value=np.NaN)

    #print('Islands results: \n {}'.format(result))
    #print('Islands target: \n {}'.format(self.results_islands))

    self.assertIsNotNone(estimator_islands)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, pd.DataFrame)
    self.assertTrue(result.equals(self.results_islands))

  def test_non_touching(self):
    """
    Test that a ConcentricRegionsEstimator object can be initialized with region data containing regions that are
    not  touching and that the results are as expected
    """
    estimation_data = EstimationData(self.sites_non_touching, self.regions_non_touching, self.actuals_non_touching)
    estimator_non_touching = ConcentricRegionsEstimator(estimation_data, verbose=0)
    self.assertEqual(estimator_non_touching.estimation_data.get_adjacent_regions(['PE']), [])
    self.assertEqual(estimator_non_touching.estimation_data.get_adjacent_regions(['TD']), [])
    result = estimator_non_touching.get_estimations('NO2_mean', None, '2019-10-15').fillna(value=np.NaN)

    #print('Non Touching: \n {}'.format(result))
    #print('Non Touching target: \n {}'.format(self.results_non_touching))

    self.assertIsNotNone(estimator_non_touching)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, pd.DataFrame)
    self.assertTrue(result.equals(self.results_non_touching))


  def test_overlapping(self):
    """
    Test that a ConcentricRegionsEstimator object can be initialized with region data containing regions that are overlapping
    and that the results are as expected
    """
    estimation_data = EstimationData(self.sites_overlap, self.regions_overlap, self.actuals_overlap)
    estimator_overlap = ConcentricRegionsEstimator(estimation_data, verbose=0)
    self.assertEqual(estimator_overlap.estimation_data.get_adjacent_regions(['AB']), ['DD', 'IV', 'PH'])
    self.assertEqual(estimator_overlap.estimation_data.get_adjacent_regions(['AB2']), ['DD', 'IV', 'PH'])
    self.assertEqual(estimator_overlap.estimation_data.get_adjacent_regions(['DD']), ['AB','AB2', 'AB3', 'PH'])
    result = estimator_overlap.get_estimations('NO2_mean', None, '2019-10-15')

    #print('Overlap: \n {}'.format(result))
    #print('Overlap target: \n {}'.format(self.results_overlap))

    self.assertIsNotNone(estimator_overlap)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, pd.DataFrame)
    self.assertTrue(result.equals(self.results_overlap))

  def test_empty_measurements(self):
    """
        Test that a ConcentricRegionsEstimator object can be initialized with actuals containing empty measurment values
        and that the results are as expected
        """
    estimation_data = EstimationData(self.sites_empty_measurements, self.regions_empty_measurements,
                                     self.actuals_empty_measurements)
    estimator = ConcentricRegionsEstimator(estimation_data, verbose=0)

    result = estimator.get_estimations('alnus', None, '2017-06-15')

    #print('Result: \n {}'.format(result))
    #print('Target: \n {}'.format(self.results_empty_measurements))

    self.assertIsNotNone(estimator)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, pd.DataFrame)
    self.assertTrue(result.fillna(np.NaN).equals(self.results_empty_measurements))
