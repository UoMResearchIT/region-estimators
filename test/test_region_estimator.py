import unittest
from os import path
from shapely import wkt
import pandas as pd

from region_estimators.region_estimator import RegionEstimator
from region_estimators.concentric_regions_estimator import ConcentricRegionsEstimator
from region_estimators.distance_simple_estimator import DistanceSimpleEstimator
from region_estimators.estimation_data import EstimationData

class TestRegionEstimator(unittest.TestCase):
  """
  Tests for the RegionEstimator abstract base class.
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

  def test_load_good_data(self):
    """
    Test that a RegionEstimator object can be initialized with good data.
    Also check that various other initializations happen within the object.
    """
    estimation_data = EstimationData(self.sites, self.regions, self.actuals)
    estimator = RegionEstimator(estimation_data, verbose=0)

    self.assertIsNotNone(estimator)
    self.assertIsNotNone(estimator.regions['sites'])

    self.assertTrue(estimator.estimation_data.site_datapoint_count('urtica', '2018-03-15') > 0)

    with self.assertRaises(NotImplementedError):
      estimator.get_estimate('urtica', None, None)

  def test_load_bad_verbose(self):
    """
    Test that a ConcentricRegionsEstimator and DistanceSimpleEstimator objects can
    be initialized with bad verbose.
    """
    estimation_data = EstimationData(self.sites, self.regions, self.actuals)
    with self.assertRaises(AssertionError):
      ConcentricRegionsEstimator(estimation_data, 'bad')

    with self.assertRaises(AssertionError):
      DistanceSimpleEstimator(estimation_data, 2.14)


  def test_load_actuals_with_bad_data(self):
    """
    Check that loading bad actuals data will fail.
    """
    bad_files = [
      'actuals_no_id.csv',
      'actuals_no_timestamp.csv',
      'actuals_no_measurements.csv',
      'actuals_bad_values.csv'
    ]

    for file in bad_files:
      with self.subTest(file=file):
        with self.assertRaises(AssertionError):
          bad_actuals = pd.read_csv(path.join(self.load_data, file))
          estimation_data = EstimationData(self.sites, self.regions, bad_actuals)
          estimator = ConcentricRegionsEstimator(estimation_data)

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
          estimation_data = EstimationData(self.sites, bad_regions, self.actuals)
          estimator = ConcentricRegionsEstimator(estimation_data)

  def test_load_sites_with_bad_data(self):
    """
    Check that loading bad site data will fail.
    """
    bad_files = [
      'sites_no_latitude.csv',
      'sites_no_longitude.csv',
      'sites_bad_latitude.csv',
      'sites_bad_longitude.csv'
    ]

    for file in bad_files:
      with self.subTest(file=file):
        with self.assertRaises(AssertionError):
          bad_sites = pd.read_csv(path.join(self.load_data, file))
          estimation_data = EstimationData(bad_sites, self.regions, self.actuals)
          DistanceSimpleEstimator(estimation_data)

  def test_get_region_sites(self):
    """
    Check that get_region_sites works with good and bad inputs
    """
    estimation_data = EstimationData(self.sites, self.regions, self.actuals)
    estimator = RegionEstimator(estimation_data)

    with self.assertRaises(AssertionError):
        # Test that region_id not in regions raises assertion error
        estimator.estimation_data.get_region_sites('WC')

    # Test a region_id known to be present in regions and has sites
    region_sites = estimator.estimation_data.get_region_sites('DG')
    self.assertEqual(region_sites, ['1023 [POLLEN]', '1023 [WEATHER]'])

    # Test a region_id known to be present in regions and does not contain sites
    region_no_sites = estimator.estimation_data.get_region_sites('AB')
    self.assertEqual(region_no_sites, [])

  def test_site_region(self):
    """
    Check that get_region_id works with good and bad inputs
    """
    estimation_data = EstimationData(self.sites, self.regions, self.actuals)
    estimator = RegionEstimator(estimation_data)

    with self.assertRaises(AssertionError):
        # Test that an invalid site_id raises assertion error
        estimator.estimation_data.get_region_id(750)
        # Test that site_id not in sites raises assertion error
        estimator.estimation_data.get_region_id('1023333 [POLLLLLLEN]')

    # Test a site_id known to be present in sites
    region_id = estimator.estimation_data.get_region_id('1023 [POLLEN]')
    self.assertEqual(region_id, 'DG')

  def test_site_and_region_index_names(self):
    """
    Check that creating new RegionEstimator with incorrectly named indexes for sites and regions
    will return error  (should be site_id and region_id)
    """
    with self.assertRaises(AssertionError):
        # Test that loading incorrect sites index name raises assertion
        sites = pd.DataFrame(self.sites)
        sites.index = sites.index.rename('site_id')
        estimator = ConcentricRegionsEstimator(sites, self.regions, self.actuals)
        # Test that loading incorrect regions index name raises assertion
        regions = pd.DataFrame(self.regions)
        regions.index = regions.index.rename('postcode')
        estimation_data = EstimationData(self.sites, regions, self.actuals)
        estimator = ConcentricRegionsEstimator(estimation_data)

  def test_max_processors(self):
    """
    Check that creating new RegionEstimator with incorrect max_processors
    """

    with self.assertRaises(AssertionError):
        # Test that loading incorrect max_processors raises assertion
        estimation_data = EstimationData(self.sites, self.regions, self.actuals)
        estimator = ConcentricRegionsEstimator(estimation_data, verbose=0, max_processors=0)
        estimator = ConcentricRegionsEstimator(estimation_data, verbose=0, max_processors=500)