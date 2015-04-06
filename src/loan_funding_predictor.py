import argparse
from KivaLoans import KivaLoans
from KivaLoan import KivaLoan
from KivaLoanFundingPredictor import KivaLoanFundingPredictor
import sys
from pymongo import MongoClient
from os.path import expanduser
from SldaTextFeatureGenerator import SldaTextFeatureGenerator
import pandas as pd
import numpy as np
from datetime import datetime
import re

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--loanIdFile', 
                        help='(INPUT) File with loan IDs for training instances, one per line',
                        action='append',
                        required=False)
    parser.add_argument('--startYear', help='Loans earlier than this year are discarded', default=1900)
    parser.add_argument('--endYear', help='Loans later than this year are discarded', default=2999)
    parser.add_argument('--logResModelFile', 
                        help='(OUTPUT) File to store the logres model for later deployment',
                        default='/tmp/kivaLoanFundingPredictor.pkl')
    args = parser.parse_args()

    loanIds = []
    loanIdsHash = {}
    if args.loanIdFile:
        for loanIdFile in args.loanIdFile:
            print >> sys.stderr, "Reading loan IDs from %s ..." % loanIdFile,
            loanIds.extend([int(line.strip()) for line in open(loanIdFile,"rb")])
            loanIdsHash.update({(loanId,1) for loanId in loanIds})
            print >> sys.stderr, "done"
    assert(len(loanIds) == len(loanIdsHash.keys()))

    
    # Retrieve all training instances by their loan id
    client = MongoClient()
    loansCollection = client.kiva.loans

    # Now read the loans from MongoDB, and create a (huge) KivaLoans object
    if len(loanIds) > 0:
        print >> sys.stderr, "Creating MongoDB cursor to collect %d loan instances by ID ..." % len(loanIds),
        print >> sys.stderr, "Total number of loan IDs read: %d" % len(loanIds)
        c = loansCollection.find({"id": {"$in": loanIds}});
    else:
        startYear = int(args.startYear)
        startDate = datetime(startYear, 1, 1, 0, 0, 0)
        endYear = int(args.endYear)
        endDate = datetime(endYear, 12, 31, 23, 59, 59)
        print >> sys.stderr, "Creating MongoDB cursor to collect instances from %d through %d ..." % (startYear, endYear),
        c = loansCollection.find({"$and" : [{"posted_date" : { "$gte" : startDate }},
                                            {"posted_date" : { "$lte" : endDate }}
                                            ]
                                  })
    print >> sys.stderr, "done"

    print >> sys.stderr, "Storing loan documents in KivaLoans instance ..."
    # Key: loanId
    # Value: the entry
    loans = KivaLoans(loanDictList=[])
    for i,loan in enumerate(c):
        if i % 1000 == 0 and i != 0:
            print >> sys.stderr, "  read %d documents ..." % i
        id = loan['id']
        loans.push(KivaLoan(dict=loan))
    print >> sys.stderr, "done"

    print >> sys.stderr, "Getting ground truth labels ...",
    groundTruthLabels = loans.getLabels()
    print >> sys.stderr, "done"
    assert(len(groundTruthLabels) == loans.getSize())
    print >> sys.stderr, "number of 0s (not fully funded) = ", len([l for l in groundTruthLabels if l == 0])
    print >> sys.stderr, "number of 1s (fully funded) = ", len([l for l in groundTruthLabels if l == 1])

    print >> sys.stderr, "Setting up sLDA feature generator ...",
    homeDir = expanduser("~")
    projectDir = "%s/%s" % (homeDir, 'work/metis_projects/passion_project/kiva_project')
    sldaBin = "%s/%s" % (homeDir, 'install/slda-master/slda')
    modelFileBin = "%s/%s" % (projectDir, 'data/predicting_funding/slda_out/final.model')
    modelFileTxt = "%s/%s" % (projectDir, 'data/predicting_funding/slda_out/final.model.text')
    dictionaryFile = "%s/%s" % (projectDir, 'data/predicting_funding/kiva_dict.txt')
    vocabFile = "%s/%s" % (projectDir, 'data/predicting_funding/kiva.lda-c.vocab')
    slda = SldaTextFeatureGenerator(modelFileBin=modelFileBin,
                                    modelFileTxt=modelFileTxt,
                                    dictionaryFile=dictionaryFile,
                                    vocabFile=vocabFile,
                                    sldaBin=sldaBin)
    print >> sys.stderr, "done"

    print >> sys.stderr, "Getting all features at once ...",
    settingsFile = "%s/%s" % (projectDir, 'data/predicting_funding/slda_settings.txt')    
    columns, allFeatures = loans.getAllFeatures(slda, settingsFile, transformCategorical=True)
    print >> sys.stderr, "done"
   
    print >> sys.stderr, "Building training DataFrame ...",
    # Preparing dataframe
    trainDF = pd.DataFrame.from_items(zip(loans.getLoanIds(), allFeatures), columns=columns, orient='index')
    print >> sys.stderr, "done"
    

#    print >> sys.stderr, "Looking for NaN in trainDF:"
#    idsOfNaN = pd.isnull(trainDF).any(1).nonzero()[0]
#    print >> sys.stderr, trainDF.ix[idsOfNaN]
#    exit(0)

    print >> sys.stderr, "columns = ", columns
    print >> sys.stderr, 'trainDF.head(3) = ', trainDF.head(3)

    print >> sys.stderr, "Feeding data to the predictor ...",
    predictor = KivaLoanFundingPredictor()
    predictor.feedDataFrames(X=trainDF, y=groundTruthLabels)
    print >> sys.stderr, "done"

    # Functions
    def runExperiment(featureGroupConfig):
        flatFeatureList = [val for featureGroup in featureGroupConfig for val in featureGroup]
        predictor.setActiveColumns(featuresToUse=flatFeatureList)
        return predictor.trainAndEvaluate(nrCrossValidationFolds=10)

    # From here on, play with various combinations of features
    featureGroups = []
    # IN ORDER OF CONTRIBUTION
    featureGroups.append(['Log10LoanAmount'])
    featureGroups.append(['topic_00', 'topic_01', 'topic_02', 'topic_03', 'topic_04', 
                          'topic_05', 'topic_06', 'topic_07', 'topic_08', 'topic_09', 
                          'topic_10', 'topic_11', 'topic_12', 'topic_13', 'topic_14', 
                          'topic_15', 'topic_16', 'topic_17', 'topic_18', 'topic_19'])
    featureGroups.append(['PostedMonthJan', 'PostedMonthFeb', 'PostedMonthMar',
                          'PostedMonthApr', 'PostedMonthMay', 'PostedMonthJun',
                          'PostedMonthJul', 'PostedMonthAug', 'PostedMonthSep',
                          'PostedMonthOct', 'PostedMonthNov', 'PostedMonthDec', ])
    featureGroups.append(['MajorityGender'])
    featureGroups.append(['Log10NumberOfBorrowers'])
    featureGroups.append(['LoansPosted','TotalAmountRaised'])
    featureGroups.append(['GeoLatitude', 'GeoLongitude'])
    featureGroups.append(['RepaymentTerm'])
    featureGroups.append(['DelinquencyRate', 'Rating'])
    featureGroups.append(['BonusCreditEligibility'])
    featureGroups.append(['Log10EnglishDescriptionLength'])

    baselineFeatureGroup = ['Baseline']

    config = []
    config.append(baselineFeatureGroup)
    experimentalResults = runExperiment(config)
    bestResult = experimentalResults[0]
    bestConfig = config
    print >> sys.stderr, "config ", config,
    print >> sys.stderr, ": ", experimentalResults
    for f in featureGroups:
        config.append(f)
        experimentalResults = runExperiment(config)
        print >> sys.stderr, "config ", config,
        print >> sys.stderr, ": ", experimentalResults
        if experimentalResults[0] > bestResult:
            bestResult = experimentalResults[0]
            bestConfig = config
            print "BETTER RESULT!"

    print "bestResult =", bestResult
    print "bestConfig =", bestConfig

    print >> sys.stderr, "Saving best classifier to disk ...",
    predictor.saveToDisk(pathToFile=args.logResModelFile)
    print >> sys.stderr, "done"

    
    print >> sys.stderr, "Preparing unseen data ...",
    unseenKivaLoans = [847571, 847570, 848289]
    unseenKivaLoanCollection = KivaLoans(unseenKivaLoans)

    columns2, unseenFeatures = unseenKivaLoanCollection.getAllFeatures(slda, settingsFile, transformCategorical=True)
    assert(columns == columns2)

    unseenDF = pd.DataFrame.from_items(zip(unseenKivaLoans, unseenFeatures), columns=columns, orient='index')
    print >> sys.stderr, "done"

    print >> sys.stderr, "Loading classifier from disk ...",
    predictor.loadFromDisk(pathToFile=args.logResModelFile)
    print >> sys.stderr, "done"

    probaList = predictor.predict_proba(X=unseenDF)
    predictions = predictor.predict(X=unseenDF)

    print >> sys.stderr, 'unseenDF.head(3) = ', unseenDF.head(3)

    print >> sys.stderr, "probaList = ", probaList
    print >> sys.stderr, "predictions = ", predictions

    activeColumns = predictor.getActiveColumns()
    modelCoefficients = predictor.getCoefficients()

    print >> sys.stderr, "active columns ", activeColumns
    print >> sys.stderr, "coefficients", modelCoefficients
    assert(len(activeColumns) == len(modelCoefficients))

    sortedFeatureCoefficients = sorted([featureCoefficient for featureCoefficient in zip(activeColumns,modelCoefficients)], 
                                       key=lambda x:x[1], 
                                       reverse=True)

    topics = slda.getTopics(nrWordsPerTopic=10, sortedByDescendingEta=False, withEtas=False, withBetas=False)
    print topics
    print >> sys.stderr, "sorted feature coefficients in trained model:"
    for sf in sortedFeatureCoefficients:
        feature, coefficient = sf
        print >> sys.stderr, sf,
        m = re.match("^topic_(\d+)$",feature)
        if m:
            topicIndex = int(m.group(1))
            print >> sys.stderr, topics[topicIndex]
        print >> sys.stderr, ""
