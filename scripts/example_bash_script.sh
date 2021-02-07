#!/bin/bash

OUTDIR='outputs'
OUTFILE_SUFFIX='2017-04-01'
METHOD='concentric-regions'
MEASUREMENT='urtica'
TIMESTAMP='2017-04-01'
REGION_ID='AB'
VERBOSE=0
MAX_PROCESSORS=3



# EXAMPLE 1
# Specifi request for single timestamp / region
ARGUMENTS_1="--outdir ${OUTDIR} --outfile_suffix ${OUTFILE_SUFFIX} --timestamp ${TIMESTAMP} --region_id ${REGION_ID} \
--method ${METHOD} --measurement ${MEASUREMENT} --verbose ${VERBOSE} --max_processors ${MAX_PROCESSORS}"
python region_estimation_script.py ${ARGUMENTS_1}

# EXAMPLE 2
# All regions timestamp request
VERBOSE=0
ARGUMENTS_2="-o ${OUTDIR} -u ${OUTFILE_SUFFIX} -t ${TIMESTAMP} -m ${METHOD} -e ${MEASUREMENT} -v ${VERBOSE} -p ${MAX_PROCESSORS}"

python region_estimation_script.py ${ARGUMENTS_2}

# EXAMPLE 3
# Timeseries style request (no timestamp)
VERBOSE=0
REGION_ID='SK'
ARGUMENTS_3="-o ${OUTDIR} -u ${OUTFILE_SUFFIX} -g ${REGION_ID} -m ${METHOD} -e ${MEASUREMENT} -v ${VERBOSE} -p ${MAX_PROCESSORS}"

python region_estimation_script.py ${ARGUMENTS_3}

# EXAMPLE 4
# Get estmates for all timestamps / regions (can be slow if we have a large dataset)
VERBOSE=0
ARGUMENTS_4="-o ${OUTDIR} -u ${OUTFILE_SUFFIX}  -m ${METHOD} -e ${MEASUREMENT} -v ${VERBOSE} -p ${MAX_PROCESSORS}"

python region_estimation_script.py ${ARGUMENTS_4}