#two_samples_test_NB.py

import numpy as np
import pandas as pd
from GPcounts_Module import Fit_GPcounts
import gpflow

import sys

import os
import tensorflow as tf

# Get number of cores reserved by the batch system (NSLOTS is automatically set, or use 1 if not)
NUMCORES=int(os.getenv("NSLOTS",1))
# print("Using", NUMCORES, "core(s)" )
# Create session properties
config=tf.compat.v1.ConfigProto(inter_op_parallelism_threads=NUMCORES,intra_op_parallelism_threads=NUMCORES)

tf.compat.v1.Session.intra_op_parallelism_threads = NUMCORES
tf.compat.v1.Session.inter_op_parallelism_threads = NUMCORES

filename = sys.argv[1]
print(filename)

likelihood = 'Negative_binomial'
X = pd.read_csv('pseudoT_8.csv',index_col=[0])
Y = pd.read_csv(filename,index_col=[0])
gp_counts = Fit_GPcounts(X,Y,safe_mode = True)
log_likelihood = gp_counts.Two_samples_test(likelihood)
log_likelihood.to_csv("ll_"+likelihood+"_"+filename)


