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
loanLenderCollection = client.kiva.loanslenders

print >> sys.stderr, "Creating MongoDB cursor ...",
c = loanLenderCollection.find()
print >> sys.stderr, "done"

columns = []
columns.append('id')
columns.append('lender_ids')

dfLoansLenders = pd.DataFrame(columns=columns)
loansLenders = []

realNrDocs = 0
for i,doc in enumerate(c):
    
    rec = {}
    for col in columns:
        rec[col] = doc[col]

    loansLenders.append(rec)
    
    if i % 50000 == 0 and i != 0:
        print >> sys.stderr, "read %d documents ..." % i
    realNrDocs += 1

dfLoansLenders = pd.DataFrame(loansLenders, columns=columns)

print >> sys.stderr, "Setting and sorting the dataframe index ..."
dfLoansLenders = dfLoansLenders.set_index(["id"], drop=True, inplace=False)
print >> sys.stderr, "done"


print >> sys.stderr, "Shape of dataframe: ", dfLoansLenders.shape
loansLendersDataFrameFile = "%s/%s_dataframe.h5" % (args.dataDir, args.baseName)
print >> sys.stderr, "Writing lenders dataframe file %s ..." % loansLendersDataFrameFile,

# See http://pandas.pydata.org/pandas-docs/dev/io.html#io-hdf5

dfLoansLenders.to_hdf(loansLendersDataFrameFile, 'table')
print >> sys.stderr, "done"
