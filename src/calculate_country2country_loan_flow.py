from pandas.io.pytables import read_hdf
import sys 
import argparse
from datetime import datetime
import pickle
from pymongo import MongoClient
import json
import csv
import re

parser = argparse.ArgumentParser()
parser.add_argument('--inDataDir', help='Directory for reading the dataframes', required=True)
parser.add_argument('--isoCountryCodesFile', help='path to TSV file with ISO country codes', required=True)
parser.add_argument('--outDataDir', help='Directory for writing the JSON file', required=True)
parser.add_argument('--outBaseName', help='Base name of the output JSON file', required=True)
parser.add_argument('--startYear', help='Loans earlier than this year are discarded', default=1900)
parser.add_argument('--endYear', help='Loans later than this year are discarded', default=2999)
parser.add_argument('--minValue', help='Cumulative loan amounts smaller this this value are not included in the JSON file', default=0)
args = parser.parse_args()

minValue = int(args.minValue)

iso2countryName = {}
iso2region = {}
isoregionCode2Name = {'eu':'Europe',
                      'na':'North America',
                      'sa':'South America',
                      'af':'Africa',
                      'as':'Asia',
                      'oc':'Oceania',
                      'unk':'Unknown',
                      'oth':'Other'
                      }

print >> sys.stderr, "Loading ISO country codes from %s ..." % args.isoCountryCodesFile,
with open(args.isoCountryCodesFile, 'rb') as tsvfile:
    ccReader = csv.reader(tsvfile, delimiter='\t')
    for row in ccReader:
        countryCode = row[0]
        regionCode = row[2]
        longCountryName = row[3]
        res = re.split(",", longCountryName)
        if len(res) > 0:
            shortCountryName = res[0]
        else:
            shortCountryName = longCountryName
        iso2countryName[countryCode.lower()] = shortCountryName
        iso2region[countryCode.lower()] = regionCode.lower()
#iso2countryName['unk'] = 'Unknown'
#iso2countryName['oth'] = 'Other'
print >> sys.stderr, "done"

client = MongoClient()
lendersCollection = client.kiva.lenders
print >> sys.stderr, "Creating MongoDB cursor on lenders collection ...",
lendersCursor = lendersCollection.find({})
print >> sys.stderr, "done"

lenders = {}
for i,lender in enumerate(lendersCursor):

    if i % 100000 == 0 and i != 0:
        print >> sys.stderr, ">>>>>>>>>>>>>>>>>>>>>>> loaded %d lenders ..." % i

    lender_id = lender['lender_id']
    lenders[lender_id] = lender

loansLendersCollection = client.kiva.loanslenders
print >> sys.stderr, "Creating MongoDB cursor on loans_lenders collection ...",
loansLendersCursor = loansLendersCollection.find({})
print >> sys.stderr, "done"

loans_lenders = {}
for i,loan_lenders in enumerate(loansLendersCursor):

    if i % 100000 == 0 and i != 0:
        print >> sys.stderr, ">>>>>>>>>>>>>>>>>>>>>>> loaded %d loan_lenders ..." % i

    loan_id = loan_lenders['id']
    loans_lenders[loan_id] = loan_lenders


loansCollection = client.kiva.loans
startYear = int(args.startYear)
startDate = datetime(startYear, 1, 1, 0, 0, 0)
endYear = int(args.endYear)
endDate = datetime(endYear, 12, 31, 23, 59, 59)
print >> sys.stderr, "Creating MongoDB cursor on loans collection ...",
loansCursor = loansCollection.find({"$and" : [{"posted_date" : { "$gte" : startDate }},
                                              {"posted_date" : { "$lte" : endDate }}
                                              ]
                                    })
print >> sys.stderr, "done"

country2country_loans = {}

for i,loan in enumerate(loansCursor):

    if i % 10000 == 0 and i != 0:
        print >> sys.stderr, ">>>>>>>>>>>>>>>>>>>>>>> processed %d loans ..." % i

    loanId = loan['id']
    loanAmount = int(loan['loan_amount'])
#    print "loanId = ", loanId
#    print "loanAmount = ", loanAmount
    postedDate = loan['posted_date']
    lenderCount = loan['lender_count']
    location_country_code = loan['location']['country_code'].lower()

#    if re.match("^[aA]",location_country_code):
#        pass
#    else:
#        continue#

    try:
        loan_lenders = loans_lenders[loanId]
        lender_ids = loan_lenders['lender_ids']
#        print "loanId = ", loanId
#        print "lenders = ", lender_ids
        if postedDate < startDate:
            print >> sys.stderr, "Discarding loan dated %s" % str(posted_date)
            continue
        else:
#            print >> sys.stderr, "OK: loan dated %s" % str(posted_date)
            pass
        if lender_ids:
            nrLenders = len(lender_ids)
            assert(nrLenders == lenderCount)
            avgLoanAmountPerLender = loanAmount/lenderCount
            for lender_id in lender_ids:
#                print "lender_id =", lender_id
                try:
                    lender_country = lenders[lender_id]['country_code'].lower()
                    if lender_country is None:
                        lender_country = "unk"
                except:
                    lender_country = "unk"

#                if re.match("^[aA]",lender_country):
#                    pass
#                else:
#                    continue



                # We don't know exactly how much each lender gave, so we take the average
                if country2country_loans.has_key(lender_country):
                    if country2country_loans[lender_country].has_key(location_country_code):
                        country2country_loans[lender_country][location_country_code] += avgLoanAmountPerLender
                    else:
                        country2country_loans[lender_country][location_country_code] = avgLoanAmountPerLender
                else:
                    country2country_loans[lender_country] = {}
                    country2country_loans[lender_country][location_country_code] = avgLoanAmountPerLender
        else:
            # Assume the loan comes from an unknown country
            lender_country = "unk"
            if country2country_loans.has_key(lender_country):
                if country2country_loans[lender_country].has_key(location_country_code):
                    country2country_loans[lender_country][location_country_code] += loanAmount
                else:
                    country2country_loans[lender_country][location_country_code] = loanAmount
            else:
                country2country_loans[lender_country] = {}
                country2country_loans[lender_country][location_country_code] = loanAmount
    except Exception, e:
#        print >> sys.stderr, "Error in finding loan %s:\n%s" % (loanId,str(e))
        pass

# Prepare JSON objects to be dumped in a format compatible with D3 visualization as in 
# https://apps.carleton.edu/career/visualize/

country2country_loans_for_d3 = {'nodes':[],
                                'links':[]}

# Move cumulative loan amounts smaller than minValue to 'other'
# This reduces the number of countries to be shown individually
lendingCountries = {}
borrowingCountries = {}
for lendingCountryCode in [lcc for lcc in country2country_loans.keys() if lcc != 'oth']:
    for lendingCountryCode, loans in country2country_loans.items():
        for borrowingCountryCode in [bcc for bcc in loans.keys() if bcc != 'oth']:
            if country2country_loans[lendingCountryCode][borrowingCountryCode] >= minValue:
                lendingCountries[lendingCountryCode.lower()] = 1
                borrowingCountries[borrowingCountryCode.lower()] = 1
            else:
                # Move this cumulative item to "other" for both lender and borrower
                lendingCountries['oth'] = 1
                borrowingCountries['oth'] = 1
                if not country2country_loans.has_key('oth'):
                    country2country_loans['oth'] = {}
                if country2country_loans['oth'].has_key('oth'):
                    country2country_loans['oth']['oth'] += country2country_loans[lendingCountryCode][borrowingCountryCode]
                else:
                    country2country_loans['oth']['oth'] = country2country_loans[lendingCountryCode][borrowingCountryCode]
                del country2country_loans[lendingCountryCode][borrowingCountryCode]

# Hardcoded, for convenience
lendingRegionCodes = ['oth','na','unk','eu','oc','as','sa','af']
borrowingRegionCodes = ['oth','as','af','sa','na','oc','eu']

# Sort by position in region list (see above), then alphabetically by country code
lendingCountries = sorted(lendingCountries.keys(), key=lambda x: (lendingRegionCodes.index(iso2region[x]),x))
borrowingCountries = sorted(borrowingCountries.keys(), key=lambda x:(borrowingRegionCodes.index(iso2region[x]),x))

print "%d lendingCountries: " % len(lendingCountries), lendingCountries
print "%d borrowingCountries: " % len(borrowingCountries), borrowingCountries

nodeCounter = 0
for lendingRegionCode in lendingRegionCodes:
    country2country_loans_for_d3['nodes'].append({'node': nodeCounter,
                                                  'name': isoregionCode2Name[lendingRegionCode.lower()]
                                                  })
    nodeCounter += 1

for lendingCountryCode in lendingCountries:
    country2country_loans_for_d3['nodes'].append({'node': nodeCounter,
                                                  'name': iso2countryName[lendingCountryCode.lower()]
                                                  })
    nodeCounter += 1
for borrowingCountryCode in borrowingCountries:
    country2country_loans_for_d3['nodes'].append({'node': nodeCounter,
                                                  'name': iso2countryName[borrowingCountryCode.lower()]
#                                                  'link': "<a class=\"pathwaysLink\"/>"
                                                      })
    nodeCounter += 1

for borrowingRegionCode in borrowingRegionCodes:
    country2country_loans_for_d3['nodes'].append({'node': nodeCounter,
                                                  'name': isoregionCode2Name[borrowingRegionCode.lower()]
                                                  })
    nodeCounter += 1

for i,lendingCountryCode in enumerate(lendingCountries):
    totalLending = 0
    linksToAdd = []
    for j,borrowingCountryCode in enumerate(borrowingCountries):
        try:
            totalLending += country2country_loans[lendingCountryCode][borrowingCountryCode]
            linksToAdd.append({'source':len(lendingRegionCodes) + i,
                               'target':len(lendingRegionCodes) + len(lendingCountries) + j,
                               'value':country2country_loans[lendingCountryCode][borrowingCountryCode]
                               })
        except Exception, e:
#            print >> sys.stderr, str(e)
            pass
    if totalLending > 0:
        # Link from lending region to lending country (simply by means of grouping)
        country2country_loans_for_d3['links'].append({'source':lendingRegionCodes.index(iso2region[lendingCountryCode]),
                                                      'target':len(lendingRegionCodes) + i,
                                                      'value':totalLending})
    # Link from lending country to borrowing country
    country2country_loans_for_d3['links'].extend(linksToAdd)

for j,borrowingCountryCode in enumerate(borrowingCountries):
    totalBorrowing = 0
    for i,lendingCountryCode in enumerate(lendingCountries):
        try:
            totalBorrowing += country2country_loans[lendingCountryCode][borrowingCountryCode]
        except Exception, e:
#            print >> sys.stderr, str(e)
            pass
    if totalBorrowing > 0:
        # Link from borrowing country to borrowing region (simply by means of grouping)
        country2country_loans_for_d3['links'].append({'source':len(lendingRegionCodes) + len(lendingCountries) + j,
                                                      'target':len(lendingRegionCodes) + len(lendingCountries) + len(borrowingCountries) + borrowingRegionCodes.index(iso2region[borrowingCountryCode]),
                                                      'value':totalBorrowing})


country2countryLoanFlowFile = "%s/%s_country2country_loan_flows.json" % (args.outDataDir, args.outBaseName)
print >> sys.stderr, "Saving result in %s ..." % country2countryLoanFlowFile,
with open(country2countryLoanFlowFile, 'wb') as jsonFile:
    json.dump(country2country_loans_for_d3, jsonFile)
print >> sys.stderr, "done"
