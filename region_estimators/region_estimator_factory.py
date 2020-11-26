# Polymorphic factory methods.
from __future__ import generators

# These region estimators must stay - despite not appearing to be used!!
from region_estimators.diffusion_estimator import DiffusionEstimator
from region_estimators.distance_simple_estimator import DistanceSimpleEstimator


class RegionEstimatorFactory:
    factories = {}

    # A Template Method:
    @staticmethod
    def create(method_name, sensors, regions, actuals, verbose=DiffusionEstimator.VERBOSE_DEFAULT):
        class_name = RegionEstimatorFactory.get_classname(method_name)
        if class_name not in RegionEstimatorFactory.factories:
            RegionEstimatorFactory.factories[class_name] = eval(class_name + '.Factory()')
        return RegionEstimatorFactory.factories[class_name].create(sensors, regions, actuals, verbose)

    region_estimator = create

    @staticmethod
    def get_classname(method_name):
        if method_name == 'diffusion':
            return 'DiffusionEstimator'
        elif method_name == 'distance-simple':
            return 'DistanceSimpleEstimator'
        else:
            raise ValueError('Method name does not exist')



