import argparse
import sys
import csv
import pandas as pd
import numpy as np
import re
from pymongo import MongoClient
from pprint import pprint
from kiva_utilities import getMajorityGender
from sklearn import preprocessing
from sklearn.cross_validation import cross_val_score, KFold
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from math import log10
import random
from urllib2 import urlopen
import json

def getKivaPartners():

    global partners
    partners = {}
    allRatings = []
    allDelinquencyRates = []

    kivaPartnersUrl = "http://api.kivaws.org/v1/partners.json"
    print >> sys.stderr, "Retrieving Kiva partner list from %s ..." % kivaPartnersUrl,
    dataStr = urlopen(kivaPartnersUrl).read()
    dataObj = json.loads(dataStr,'utf-8')

    print >> sys.stderr, "parsing it ...",
    for partner in dataObj['partners']:
        partnerId = partner['id']
        partners[partnerId] = partner
        if partner['status'] in ['active','paused']:
            try:
                rating = float(partner['rating'])
                allRatings.append(rating)
            except:
                pass
            try:
                delinquencyRate = float(partner['delinquency_rate'])
                allDelinquencyRates.append(delinquencyRate)
            except:
                pass
    print >> sys.stderr, "done"
    
    global avgPartnerRating
    avgPartnerRating = sum(allRatings)/float(len(allRatings))
    global avgPartnerDelinquencyRate
    avgPartnerDelinquencyRate = sum(allDelinquencyRates)/float(len(allDelinquencyRates))
    
    pprint(partners[185])

def getPartnerDelinquencyRate(loan):

    result = -1

    try:
        delinquencyRate = partners[loan['partner_id']]['delinquency_rate']
        result = float(delinquencyRate)
    except:
        result = avgPartnerDelinquencyRate

    assert(result >= 0.0)
    return result

def getPartnerRating(loan):

    result = -1

    try:
        rating = partners[loan['partner_id']]['rating']
        result = float(rating)
    except:
        result = avgPartnerRating

    assert(result >= 0.0)
    return result

def initialize():

    global feat2func
    # Dictionary of extra features (i.e. on top of sLDA ones), with lambda function
    # that specifies how/where to get them (from an individual Kiva loan object)
    feat2func = {'borrower_majority_gender':lambda loan: 1 if getMajorityGender(loan['borrowers']) == u'F' else 0,
                 'loan_amount':lambda loan:log10(loan['loan_amount']),
                 'bonus_credit_eligibility':lambda loan: 1 if loan['bonus_credit_eligibility'] else 0,
                 'nr_borrowers':lambda loan:log10(len(loan['borrowers'])),
                 'translated':lambda loan: 1 if loan.has_key('translator') else 0,
                 'disbursal_amount':lambda loan:loan['terms']['disbursal_amount'],
                 'disbursal_ratio':lambda loan:float(loan['terms']['disbursal_amount'])/float(loan['loan_amount']),
                 'repayment_term':lambda loan:loan['terms']['repayment_term'],
                 'posted_month':lambda loan:loan['posted_date'].month,
                 'posted_day_of_month':lambda loan:loan['posted_date'].day,
                 'has_image':lambda loan: 1 if loan['image'] else 0,
                 'geo_lat':lambda loan: float(re.split("\s+",loan['location']['geo']['pairs'])[0]),
                 'geo_lon':lambda loan: float(re.split("\s+",loan['location']['geo']['pairs'])[1]),
                 'en_description_length':lambda loan: log10(1) if not loan['description']['texts'].has_key('en') else log10(len(re.split("\s+",loan['description']['texts']['en']))),
                 'partner_rating':lambda loan: getPartnerRating(loan),
                 'partner_delinquency_rate':lambda loan: getPartnerDelinquencyRate(loan),
                 'partner_loans_posted':lambda loan: log10(partners[loan['partner_id']]['loans_posted']),
                 'partner_total_amount_raised':lambda loan: log10(partners[loan['partner_id']]['total_amount_raised']),
                 'constant':lambda loan:1
                 }

    global args

    parser = argparse.ArgumentParser()

    parser.add_argument('--trainSldaGammaFile', 
                        help='(INPUT) File with with gammas representing posterior Dirichlets from sLDA for training instances',
                        required=True)
    parser.add_argument('--trainLabelFile', 
                        help='(INPUT) File with label for training instances, one per line', 
                        required=True)
    parser.add_argument('--trainIdFile', 
                        help='(INPUT) File with loan IDs for training instances, one per line', 
                        required=True)

    parser.add_argument('--testSldaGammaFile', 
                        help='(INPUT) File with with gammas representing posterior Dirichlets from sLDA for test instances', 
                        required=True)
    parser.add_argument('--testLabelFile', 
                        help='(INPUT) File with label for test instances, one per line', 
                        required=True)
    parser.add_argument('--testIdFile', 
                        help='(INPUT) File with loan IDs for test instances, one per line', 
                        required=True)

    global featureChoices
    featureChoices = ['slda']
    featureChoices.extend(feat2func.keys())
    featureChoices = sorted(featureChoices)

    parser.add_argument('--feat', 
                        help='Name of the feature to include', 
                        choices=featureChoices, 
                        action="append")
    
    args = parser.parse_args()

    

def prepareData(sldaGammaFile, labelFile, loanIdFile):

    print >> sys.stderr, "Reading sLDA gamma values from %s ..." % sldaGammaFile,
    gammas = [[float(gamma) for gamma in instance] for instance in [re.split("\s+",line.strip()) for line in open(sldaGammaFile,"rb")]]
    print >> sys.stderr, "done"

    print >> sys.stderr, "Reading loan IDs from %s ..." % loanIdFile,
    loanIds = [int(line.strip()) for line in open(loanIdFile,"rb")]
    loanIdsHash = {(loanId,1) for loanId in loanIds}
    print >> sys.stderr, "done"

    assert(len(gammas) == len(loanIds))

    if 'slda' in args.feat:
        DF = pd.DataFrame.from_items(zip(loanIds, gammas), columns=["topic_%03d" % (i+1) for i in range(len(gammas[0]))], orient='index')
    else:
        DF = pd.DataFrame(index=loanIds)
#    print DF.head(3)

    # Retrieve all training instances by their loan id
    client = MongoClient()
    loansCollection = client.kiva.loans

    print >> sys.stderr, "Creating MongoDB cursor to collect %d loan instances by ID ..." % len(loanIds),
    c = loansCollection.find({"id": {"$in": loanIds}});
    print >> sys.stderr, "done"

    print >> sys.stderr, "Storing loan documents in an associative list ...",
    # Key: loanId
    # Value: the entry
    loans = {}
    for i,loan in enumerate(c):
        id = loan['id']
        loans[int(id)] = loan
    print >> sys.stderr, "done"

    assert(len(loanIds) == len(loans.keys())), "expected equal number of loanIds (%d) and keys in associative array loans (%d)" % (len(loanIds), len(loans.keys()))

    #pprint(loans[loanIds[0]])

    extraColumns = []
    for f in featureChoices:
        if f in args.feat and f != 'slda':
            extraColumns.append(f)
    #print columns

    extraFeatures = []
    for i,loanId in enumerate(loanIds):
        loan = loans[loanId]
        entry = []

        for f in featureChoices:
            if f in args.feat and f != 'slda':
                func = feat2func[f]
                entry.append(func(loan))
    
        extraFeatures.append((loanId,entry))

    extraDF = pd.DataFrame.from_items(extraFeatures, columns=extraColumns, orient='index')
#    print extraDF.head(3)

    mergedDF = pd.concat([DF, extraDF],axis=1)
#    print mergedDF.head(3)

    #print mergedDF.shape


    print >> sys.stderr, "Reading labels from %s ..." % labelFile,
    labels = [int(line.strip()) for line in open(labelFile,"rb")]
    print >> sys.stderr, "done"

    return (mergedDF,labels)

def prepareTrainData():
    return prepareData(sldaGammaFile=args.trainSldaGammaFile, 
                       labelFile=args.trainLabelFile,
                       loanIdFile=args.trainIdFile)

def prepareTestData():
    return prepareData(sldaGammaFile=args.testSldaGammaFile, 
                       labelFile=args.testLabelFile,
                       loanIdFile=args.testIdFile)

def trainAndEvaluateClassifier(X,y):

    assert(X.shape[0] == len(y))

    cValues = [pow(10,x) for x in range(10)]

    # selects weights inversely proportional to class frequencies in the training set
    # See http://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
    #classWeight = 'auto'
    classWeight = None

    scorerType = 'roc_auc'
#    scorerType = 'f1'
#    scorerType = 'accuracy'
    nrCrossValidationFolds=10

    # We shuffle to be sure
    cvGenerator = KFold(len(X), n_folds=nrCrossValidationFolds, shuffle=True)

    estimators = []
    scoreList = []
    for i in range(len(cValues)):
        c = cValues[i]
        print >> sys.stderr, "(%d/%d) Building logres model for C value %1.15f ..." % (i+1,len(cValues),c),
        estimator = LogisticRegression(C=c,class_weight=classWeight)
        print >> sys.stderr, "applying it ...",
        scores = cross_val_score(estimator, X, y=y, scoring=scorerType, cv=cvGenerator, n_jobs=1)
        estimators.append(estimator)
        scoreList.append((scores.mean(),scores.std()))
        print >> sys.stderr, "done"

    print "scoreList = ", scoreList
    meanScores = [x[0] for x in scoreList]

    bestModelIndex = meanScores.index(max(meanScores))
    print "best logres model has:"
    print "%s score: %2.2f%% (+/- %2.2f%%)" % (scorerType, scoreList[bestModelIndex][0] * 100, scoreList[bestModelIndex][1] * 100)
    bestCValue = cValues[bestModelIndex]
    bestLogCValue = log10(bestCValue)
    print "C value: ", bestCValue
    print "log10(C) value: ", bestLogCValue

# build binary classifier with logres and/or other methods
# SAVE MODEL(S) ON DISK (so it can be deployed, e.g. behind a Flask web server)

if __name__ == "__main__":
    
    getKivaPartners()

    initialize()

    X_train, y_train = prepareTrainData()
    X_train_scaled = preprocessing.scale(X_train.astype(float), copy=False)

    X_test, y_test = prepareTestData()
    X_test_scaled = preprocessing.scale(X_test.astype(float), copy=False)

    # Let's recombine train and test, since we are going to perform cross validation anyway
    X = pd.concat([X_train, X_test],axis=0)
    X_scaled = preprocessing.scale(X.astype(float), copy=False)
    y = y_train
    y.extend(y_test)

#    print X.head(3)
#    print X.tail(3)
#    print X.shape

    trainAndEvaluateClassifier(X_scaled,y)
