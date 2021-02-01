# Polymorphic factory methods.
from __future__ import generators

# These region estimators must stay - despite not appearing to be used!!
from region_estimators.concentric_regions_estimator import ConcentricRegionsEstimator
from region_estimators.distance_simple_estimator import DistanceSimpleEstimator
from region_estimators.region_estimator import RegionEstimator

available_methods = {'concentric-regions': ConcentricRegionsEstimator,
                    'distance-simple': DistanceSimpleEstimator}

class RegionEstimatorFactory:
    factories = {}

    # A Template Method:
    @staticmethod
    def create(method_name, estimation_data, verbose=ConcentricRegionsEstimator.VERBOSE_DEFAULT,
               max_processors=RegionEstimator.MAX_NUM_PROCESSORS):
        class_name = RegionEstimatorFactory.get_classname(method_name)
        if class_name not in RegionEstimatorFactory.factories:
            RegionEstimatorFactory.factories[class_name] = eval(class_name + '.Factory()')
        return RegionEstimatorFactory.factories[class_name].create(estimation_data, verbose, max_processors)

    region_estimator = create

    @staticmethod
    def get_classname(method_name):
        try:
            return available_methods[method_name].__name__
        except:
            raise ValueError('Method name {} does not exist. Available methods: \n{}'.format(method_name,
                                                                                             available_methods.keys()))

    @staticmethod
    def get_available_methods():
        return available_methods.keys()



