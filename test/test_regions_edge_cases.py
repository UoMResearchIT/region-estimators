import unittest
from os import path
from shapely import wkt
import pandas as pd

from region_estimators.region_estimator import RegionEstimator

class TestRegionEdgeCases(unittest.TestCase):
  """
  Tests for the Regions file edge cases
  """

  def setUp(self):
    dir, _ = path.split(__file__)
    self.load_data_path = path.join(dir, 'data', 'loading', 'edge_cases')

    self.sensors_islands = pd.read_csv(
      path.join(self.load_data_path, 'sensors_islands.csv'),
      index_col='sensor_id'
    )

    self.sensors_touching = pd.read_csv(
      path.join(self.load_data_path, 'sensors_touching.csv'),
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

    self.actuals_touching = pd.read_csv(
      path.join(self.load_data_path, 'actuals_touching.csv')
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

    self.regions_touching = pd.read_csv(
      path.join(self.load_data_path, 'regions_touching.csv'),
      index_col='region_id'
    )
    self.regions_touching['geometry'] = self.regions_touching.apply(
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

  def test_islands(self):
    """
    Test that a RegionEstimator object can be initialized with region data containing islands
    and that the results are as expected for islands
    """
    estimator = RegionEstimator(self.sensors_islands, self.regions_islands, self.actuals_islands)

    self.assertIsNotNone(estimator)

  def test_touching(self):
    """
    Test that a RegionEstimator object can be initialized with region data containing regions that are all touching
    and that the results are as expected
    """
    estimator = RegionEstimator(self.sensors_touching, self.regions_touching, self.actuals_touching)

    self.assertIsNotNone(estimator)

  def test_non_touching(self):
    """
    Test that a RegionEstimator object can be initialized with region data containing regions that are not
    touching and that the results are as expected
    """
    estimator = RegionEstimator(self.sensors_non_touching, self.regions_non_touching, self.actuals_non_touching)

    self.assertIsNotNone(estimator)

  def test_overlapping(self):
    """
    Test that a RegionEstimator object can be initialized with region data containing regions that are overlapping
    and that the results are as expected
    """
    estimator = RegionEstimator(self.sensors_overlap, self.regions_overlap, self.actuals_overlap)

    self.assertIsNotNone(estimator)