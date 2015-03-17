import pandas as pd
import numpy as np
import sys
from pymongo import MongoClient
from datetime import datetime
from pandas.io.pytables import to_hdf

from kiva_utilities import getMajorityGender

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--dataDir', help='Directory for writing the dataframe', required=True)
parser.add_argument('--baseName', help='Base name for the dataframe file', required=True)
parser.add_argument('--startYear', help='Get all documents starting with this year', default=2015)
args = parser.parse_args()

client = MongoClient()
loansCollection = client.kiva.loans

langCode = "en"
langName="english"
loansCollection = client.kiva.loans

startYear = int(args.startYear)
start = datetime(startYear, 1, 1)
print >> sys.stderr, "Creating MongoDB cursor ...",
c = loansCollection.find({"$and" : [{"posted_date" : { "$gte" : start }},
                                    {"processed_description.texts.%s" % langCode :{'$exists': True}}
                                    ]
                          })
print >> sys.stderr, "done"

columns = []
columns.append('id')
columns.append('borrower_majority_gender')
columns.append('loan_amount')
columns.append('funded_amount')
columns.append('posted_date')
columns.append('planned_expiration_date')
columns.append('location_country_code')

dfLoans = pd.DataFrame(columns=columns)
loans = []

realNrDocs = 0
for i,c in enumerate(c):
    id = c['id']
    borrowersMajorityGender = getMajorityGender(c['borrowers'])
    loanAmount = c[u'loan_amount']
    fundedAmount = c[u'funded_amount']
    postedDate = c[u'posted_date']
    plannedExpirationDate = c[u'planned_expiration_date']
    locationCountryCode = c[u'location'][u'country_code']
    
    loans.append({'id':id, 
                  'borrower_majority_gender':borrowersMajorityGender, 
                  'loan_amount':loanAmount, 
                  'funded_amount':fundedAmount, 
                  'posted_date':postedDate, 
                  'planned_expiration_date':plannedExpirationDate, 
                  'location_country_code':locationCountryCode})
    
    if i % 50000 == 0 and i != 0:
        print >> sys.stderr, "read %d documents ..." % i
    realNrDocs += 1

dfLoans = pd.DataFrame(loans, columns=columns)

print >> sys.stderr, "Setting and sorting the dataframe index ..."
dfLoans = dfLoans.set_index(["id"], drop=True, inplace=False)
print >> sys.stderr, "done"


print >> sys.stderr, "Shape of dataframe: ", dfLoans.shape
loansDataFrameFile = "%s/%s_dataframe.h5" % (args.dataDir, args.baseName)
print >> sys.stderr, "Writing loans dataframe file %s ..." % loansDataFrameFile,

# See http://pandas.pydata.org/pandas-docs/dev/io.html#io-hdf5

dfLoans.to_hdf(loansDataFrameFile, 'table')
print >> sys.stderr, "done"
