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

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--loanIdFile', 
                        help='(INPUT) File with loan IDs for training instances, one per line',
                        action='append',
                        required=True)
    parser.add_argument('--logResModelFile', 
                        help='(OUTPUT) File to store the logres model for later deployment',
                        default='/tmp/kivaLoanFundingPredictor.pkl')
    args = parser.parse_args()

    loanIds = []
    loanIdsHash = {}
    for loanIdFile in args.loanIdFile:
        print >> sys.stderr, "Reading loan IDs from %s ..." % loanIdFile,
        loanIds.extend([int(line.strip()) for line in open(loanIdFile,"rb")])
        loanIdsHash.update({(loanId,1) for loanId in loanIds})
        print >> sys.stderr, "done"
    assert(len(loanIds) == len(loanIdsHash.keys()))
    print >> sys.stderr, "Total number of loan IDs read: %d" % len(loanIds)

    
    # Retrieve all training instances by their loan id
    client = MongoClient()
    loansCollection = client.kiva.loans

    # Now read the loans from MongoDB, and create a (huge) KivaLoans object
    print >> sys.stderr, "Creating MongoDB cursor to collect %d loan instances by ID ..." % len(loanIds),
    c = loansCollection.find({"id": {"$in": loanIds}});
    print >> sys.stderr, "done"

    print >> sys.stderr, "Storing loan documents KivaLoans instance ..."
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

    predictor.trainAndEvaluate(nrCrossValidationFolds=10)

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
