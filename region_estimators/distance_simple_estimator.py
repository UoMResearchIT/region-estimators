import pandas as pd
import geopandas as gpd

from region_estimators.region_estimator import RegionEstimator


class DistanceSimpleEstimator(RegionEstimator):

    def __init__(self, sites, regions, actuals, verbose=RegionEstimator.VERBOSE_DEFAULT):
        super(DistanceSimpleEstimator, self).__init__(sites, regions, actuals, verbose)

    class Factory:
        def create(self, sites, regions, actuals, verbose=RegionEstimator.VERBOSE_DEFAULT):
            return DistanceSimpleEstimator(sites, regions, actuals, verbose)


    def get_estimate(self, measurement, timestamp, region_id, ignore_site_ids=[]):
        """  Find estimations for a region and timestamp using the simple distance method: value of closest actual site

            :param measurement: measurement to be estimated (string, required)
            :param timestamp:  timestamp identifier (string)
            :param region_id: region identifier (string)
            :param ignore_site_ids: site id(s) to be ignored during the estimations

            :return: tuple containing
                i) estimate
                ii) dict: {'closest_site_ids': [IDs of closest site(s)]}

        """
        result = None, {'closest_site_data': None}

        # Get the actual values
        df_actuals = self.actuals.loc[
            (~self.actuals['site_id'].isin(ignore_site_ids)) &
            (self.actuals['timestamp'] == timestamp) &
            (self.actuals[measurement].notnull())
        ]

        df_sites = self.sites.reset_index()

        df_actuals = pd.merge(left=df_actuals,
                           right= df_sites,
                           on='site_id',
                           how='left')
        gdf_actuals = gpd.GeoDataFrame(data=df_actuals, geometry='geometry')

        # Get the closest site to the region
        if len(gdf_actuals) > 0:
            # Get region geometry
            df_reset = pd.DataFrame(self.regions.reset_index())
            regions_temp = df_reset.loc[df_reset['region_id'] == region_id]
            if len(regions_temp.index) > 0:
                region = regions_temp.iloc[0]

            # Calculate distances
            gdf_actuals['distance'] = pd.DataFrame(gdf_actuals['geometry'].distance(region.geometry))

            # Get site(s) with shortest distance
            top_result = gdf_actuals.sort_values(by=['distance'], ascending=True).iloc[0] #returns the whole row as a series

            if top_result is not None:
                # Take the average of all sites with the closest distance
                closest_sites = gdf_actuals.loc[gdf_actuals['distance'] == top_result['distance']]
                closest_values_mean = closest_sites[measurement].mean(axis=0)

                # In extra data, return closest site name if it exists, otherwise closest site id
                if 'name' in list(closest_sites.columns):
                    closest_sites_result = list(closest_sites['name'])
                else:
                    closest_sites_result = list(closest_sites['site_id'])

                result = closest_values_mean, {'closest_sites': closest_sites_result}

        return result
