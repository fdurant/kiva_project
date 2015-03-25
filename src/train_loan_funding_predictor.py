import argparse
import sys
import csv

parser = argparse.ArgumentParser()
parser.add_argument('--trainSldaGammaFile', help='(INPUT) File with with gammas representing posterior Dirichlets from sLDA for training instances', required=True)
parser.add_argument('--trainLabelFile', help='(INPUT) File with label for training instances, one per line', required=True)
parser.add_argument('--trainIdFile', help='(INPUT) File with loan IDs for training instances, one per line', required=True)
parser.add_argument('--loansDataFrameFile', help='(INPUT) File with all loans, in HD5 format', required=True)

args = parser.parse_args()

# TODO
# Build X dataframe containing IDs from args.trainIDfile, with features from:
# * args.trainSldaGammaFile
# * extra columns (better too many than too few!) from args.loansDataFrameFile (mongodb is an alternative, in case of performance problems)
# NORMALIZE COLUMNS (between 0 and 1)

# Build y from args.trainLabelFile

# build binary classifier with logres and/or other methods
# SAVE MODEL(S) ON DISK (so it can be deployed, e.g. behind a Flask web server)

# EVALUATION AND DEPLOYMENT WILL BE DONE IN/BY SEPARATE SCRIPTS
