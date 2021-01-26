# Polymorphic factory methods.
from __future__ import generators

# These region estimators must stay - despite not appearing to be used!!
from region_estimators.concentric_regions_estimator import ConcentricRegionsEstimator
from region_estimators.distance_simple_estimator import DistanceSimpleEstimator


class RegionEstimatorFactory:
    factories = {}

    # A Template Method:
    @staticmethod
    def create(method_name, sites, regions, actuals, verbose=ConcentricRegionsEstimator.VERBOSE_DEFAULT):
        class_name = RegionEstimatorFactory.get_classname(method_name)
        if class_name not in RegionEstimatorFactory.factories:
            RegionEstimatorFactory.factories[class_name] = eval(class_name + '.Factory()')
        return RegionEstimatorFactory.factories[class_name].create(sites, regions, actuals, verbose)

    region_estimator = create

    @staticmethod
    def get_classname(method_name):
        if method_name == 'concentric-regions':
            return 'ConcentricRegionsEstimator'
        elif method_name == 'distance-simple':
            return 'DistanceSimpleEstimator'
        else:
            raise ValueError('Method name does not exist')



