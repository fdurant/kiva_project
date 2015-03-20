import pandas as pd
import numpy as np
import sys
from pymongo import MongoClient
from datetime import datetime
from pandas.io.pytables import to_hdf

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--dataDir', help='Directory for writing the dataframe', required=True)
parser.add_argument('--baseName', help='Base name for the dataframe file', required=True)
args = parser.parse_args()

client = MongoClient()
lendersCollection = client.kiva.lenders

print >> sys.stderr, "Creating MongoDB cursor ...",
c = lendersCollection.find()
print >> sys.stderr, "done"

columns = []
columns.append('lender_id')
columns.append('name')
columns.append('whereabouts')
columns.append('country_code')
columns.append('uid')
columns.append('member_since')
columns.append('personal_url')
columns.append('occupation')
columns.append('loan_because')
columns.append('occupational_info')
columns.append('loan_count')
columns.append('invitee_count')
columns.append('inviter_id')

dfLenders = pd.DataFrame(columns=columns)
lenders = []

realNrDocs = 0
for i,doc in enumerate(c):
    
    rec = {}
    for col in columns:
        rec[col] = doc[col]

    lenders.append(rec)
    
    if i % 50000 == 0 and i != 0:
        print >> sys.stderr, "read %d documents ..." % i
    realNrDocs += 1

dfLenders = pd.DataFrame(lenders, columns=columns)

print >> sys.stderr, "Setting and sorting the dataframe index ..."
dfLenders = dfLenders.set_index(["lender_id"], drop=True, inplace=False)
print >> sys.stderr, "done"


print >> sys.stderr, "Shape of dataframe: ", dfLenders.shape
lendersDataFrameFile = "%s/%s_dataframe.h5" % (args.dataDir, args.baseName)
print >> sys.stderr, "Writing lenders dataframe file %s ..." % lendersDataFrameFile,

# See http://pandas.pydata.org/pandas-docs/dev/io.html#io-hdf5

dfLenders.to_hdf(lendersDataFrameFile, 'table')
print >> sys.stderr, "done"
