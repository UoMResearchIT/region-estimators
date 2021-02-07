from shapely import wkt
import pandas as pd
from region_estimators import RegionEstimatorFactory, EstimationData
import argparse
import os

DEFAULT_REGIONS_FILESPEC = '../sample_input_files/df_regions.csv'
DEFAULT_SITES_FILESPEC = '../sample_input_files/df_sites.csv'
DEFAULT_ACTUALS_FILESPEC = '../sample_input_files/df_actuals.csv'
DEFAULT_OUT_DIR = 'output'
DEFAULT_OUT_FILE_SUFFIX = 'output'
DEFAULT_VERBOSE = 0
DEFAULT_MAX_PROCESSORS = 1
DEFAULT_MEASUREMENT = 'urtica'
DEFAULT_METHOD = 'concentric-regions'
DEFAULT_TIMESTAMP = None
DEFAULT_REGION_ID = None

if __name__ == '__main__':
    # read arguments from the command line
    parser = argparse.ArgumentParser(
        description="*** A a Python library to calculate regional estimations of scalar quantities, based on some \
            known scalar quantities at specific locations. ***")

    parser.add_argument("--regions_filespec", "-r", type=str,
                        help="filespec of the regions metadata file (csv). Default: {}".format(DEFAULT_REGIONS_FILESPEC))
    parser.add_argument("--sites_filespec", "-s", type=str,
                        help="filespec of the sites metadata file (csv). Default: {}".format(DEFAULT_SITES_FILESPEC))
    parser.add_argument("--actuals_filespec", "-a", type=str,
                        help="filespec of the actuals data file (csv). Default: {}".format(DEFAULT_ACTUALS_FILESPEC))

    parser.add_argument("--method", "-m", dest="method", type=str,
                        help="Estimation method to use. Default: {}".format(DEFAULT_METHOD))
    parser.add_argument("--measurement", "-e", dest="measurement", type=str,
                        help="Which measurement to estimate. Default: {}".format(DEFAULT_MEASUREMENT))
    parser.add_argument("--timestamp", "-t", dest="timestamp", type=str,
                        help="Which timestamp to estimate. Default: {}".format(DEFAULT_TIMESTAMP))
    parser.add_argument("--region_id", "-g", dest="region_id", type=str,
                        help="ID of the region to estimate. Default: {}".format(DEFAULT_REGION_ID))

    parser.add_argument("--save_to_csv", dest="save_to_csv", action='store_true',
                        help="save output into CSV format (default).")
    parser.add_argument("--no_save_to_csv", dest="save_to_csv", action='store_false',
                        help="don't save output to CSV format")
    parser.set_defaults(save_to_csv=True)

    # output directory/file names
    parser.add_argument("--outdir_name", "-o", dest="outdir_name", type=str,
                        help="output directory name. Default: {}".format(DEFAULT_OUT_DIR))
    parser.add_argument("--outfile_suffix", "-u", dest="outfile_suffix", type=str,
                        help="suffix to be appended to output file name. Default: {}".format(
                            DEFAULT_OUT_FILE_SUFFIX))
    # Maximum no of processor
    parser.add_argument("--max_processors", "-p", type=int,
                        help="Maximum number of processors. Default: {}".format(
                            DEFAULT_MAX_PROCESSORS))
    # Log verbose-ness
    parser.add_argument("--verbose", "-v", dest='verbose', type=int,
                        help="Level of output for debugging (Default: {} (0 = no verbose output))".format(
                            DEFAULT_VERBOSE))

    # read arguments from the command line
    args = parser.parse_args()

    if args.regions_filespec:
        regions_filespec = args.regions_filespec
        print('Regions filespec: {}'.format(regions_filespec))
    else:
        print('No regions_filespec given, so will use {}.'.format(DEFAULT_REGIONS_FILESPEC))
        regions_filespec = DEFAULT_REGIONS_FILESPEC

    if args.sites_filespec:
        sites_filespec = args.sites_filespec
        print('Sites filespec: {}'.format(sites_filespec))
    else:
        print('No sites_filespec given, so will use {}.'.format(DEFAULT_SITES_FILESPEC))
        sites_filespec = DEFAULT_SITES_FILESPEC

    if args.actuals_filespec:
        actuals_filespec = args.actuals_filespec
        print('Actuals filespec: {}'.format(regions_filespec))
    else:
        print('No actuals_filespec given, so will use {}.'.format(DEFAULT_ACTUALS_FILESPEC))
        actuals_filespec = DEFAULT_ACTUALS_FILESPEC

    if args.method:
        method = args.method
        print('Method: {}'.format(method))
    else:
        print('No method given, so will use {}.'.format(DEFAULT_METHOD))
        method = DEFAULT_METHOD

    if args.measurement:
        measurement = args.measurement
        print('Measurement: {}'.format(measurement))
    else:
        print('No measurement given, so will use {}.'.format(DEFAULT_MEASUREMENT))
        measurement = DEFAULT_MEASUREMENT

    if args.timestamp:
        timestamp = args.timestamp
        print('Timestamp: {}'.format(timestamp))
    else:
        print('No timestamp given, so will use {}.'.format(DEFAULT_TIMESTAMP))
        timestamp = DEFAULT_TIMESTAMP

    if args.region_id:
        region_id= args.region_id
        print('region_id: {}'.format(region_id))
    else:
        print('No region_id given, so will use {}.'.format(DEFAULT_REGION_ID))
        region_id = DEFAULT_REGION_ID

    print('Save to csv: {}'.format(args.save_to_csv))

    if args.outdir_name:
        outdir_name = args.outdir_name
        print('outdir_name: {}'.format(outdir_name))
    else:
        print('No outdir_name given, so will use default: {}'.format(DEFAULT_OUT_DIR))
        outdir_name = DEFAULT_OUT_DIR

    if args.outfile_suffix:
        outfile_suffix = args.outfile_suffix
        print('outfile_suffix: {}'.format(outfile_suffix))
    else:
        print('No outfile_suffix provided, so using default: {}'.format(str(DEFAULT_OUT_FILE_SUFFIX)))
        outfile_suffix = DEFAULT_OUT_FILE_SUFFIX

    if args.max_processors:
        max_processors = max(args.max_processors, 0)
        print('max_processors: ', max_processors)
    else:
        print('No max_processors number provided, so using default: {}'.format(str(DEFAULT_MAX_PROCESSORS)))
        max_processors = DEFAULT_MAX_PROCESSORS

    if args.verbose:
        verbose = max(args.verbose, 0)
        print('verbose: ', verbose)
    else:
        print('No verbose flag provided, so using default: {}'.format(str(DEFAULT_VERBOSE)))
        verbose = DEFAULT_VERBOSE

    # Prepare input files  (For sample input files, see the 'sample_input_files' folder)
    df_regions = pd.read_csv(regions_filespec, index_col='region_id')
    df_sites = pd.read_csv(sites_filespec, index_col='site_id')
    df_actuals = pd.read_csv(actuals_filespec)

    # Convert the regions geometry column from string to wkt format using wkt
    df_regions['geometry'] = df_regions.apply(lambda row: wkt.loads(row.geometry), axis=1)

    # Create estimator, the first parameter is the estimation method.

    estimation_data = EstimationData(df_sites, df_regions, df_actuals)

    estimator = RegionEstimatorFactory.region_estimator(method, estimation_data, verbose, max_processors)

    # Make estimations
    df_estimates = estimator.get_estimations(measurement, region_id, timestamp)

    print(df_estimates)

    # Convert dataframe result to (for example) a csv file:
    if args.save_to_csv:
        df_estimates.to_csv(os.path.join(outdir_name, 'estimates_{}.csv'.format(outfile_suffix)))
