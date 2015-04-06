import numpy as np
import pandas as pd
from sklearn import preprocessing
from sklearn.cross_validation import cross_val_score, KFold
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from KivaLoan import KivaLoan
from KivaLoans import KivaLoans
from KivaPartners import KivaPartners
from SldaTextFeatureGenerator import SldaTextFeatureGenerator
import sys
from os.path import expanduser
import pickle
from math import log10

class KivaLoanFundingPredictor(object):
    ''' Class representing a predictor for Kiva Loan Funding
    The predictor can be:
    - fed with training data
    - trained
    - evaluated
    - saved to disk
    - loaded from disk
    - used on unseen examples
    '''

    def __init__(self):
        pass
    
    def setActiveColumns(self, featuresToUse=['Baseline']):
        if featuresToUse:
            self.activeColumnIndices = [i for i in range(len(self.columns)) if self.columns[i] in featuresToUse]
        else:
            self.activeColumnIndices = range(len(self.columns))        

    def getAvailableColumns(self):
        return self.columns

    def getActiveColumns(self):
        return [self.columns[i] for i in self.activeColumnIndices]

    def feedDataFrames(self, X, y):
        assert(type(X) == type(pd.DataFrame()))
        assert(type(y) in [type(pd.Series()), type([])])
        assert(X.shape[0] == len(y))

        self.columns = X.columns.values
        self.activeColumnIndices = range(len(self.columns))

        # We store the scaler so we can reapply it at runtime at unseen instances!
        # See http://scikit-learn.org/stable/modules/preprocessing.html
        self.scaler = preprocessing.StandardScaler(copy=False).fit(X)
        X_scaled = self.scaler.transform(X.astype(float))

        self.X = X_scaled
        self.y = y
    
    def train(self, estimator=LogisticRegression(C=1,class_weight='auto')):
        # Necessary for logistic regression

        self.estimator = estimator
        self.estimator.fit(self.X[:,self.activeColumnIndices],self.y)

    def trainAndEvaluate(self, 
                         cValues=[pow(10,x-10) for x in range(20)], 
                         classWeight='auto', 
                         scorerType='roc_auc', 
                         nrCrossValidationFolds=10):

        cvGenerator = KFold(len(self.X), n_folds=nrCrossValidationFolds, shuffle=True)

        estimators = []
        scoreList = []
        for i in range(len(cValues)):
            c = cValues[i]
            print >> sys.stderr, "(%d/%d) Building logres model for C value %1.15f ..." % (i+1,len(cValues),c),
            estimator = LogisticRegression(C=c,class_weight=classWeight)
            print >> sys.stderr, "applying it ...",
            scores = cross_val_score(estimator, self.X[:,self.activeColumnIndices], y=self.y, scoring=scorerType, cv=cvGenerator, n_jobs=1)
            estimators.append(estimator)
            scoreList.append((scores.mean(),scores.std()))
            print >> sys.stderr, "done"

        meanScores = [x[0] for x in scoreList]

        bestModelIndex = meanScores.index(max(meanScores))
        print >> sys.stderr, "best logres model has:"
        print >> sys.stderr,  "%s score: %2.2f%% (+/- %2.2f%%)" % (scorerType, 
                                                                   scoreList[bestModelIndex][0] * 100, 
                                                                   scoreList[bestModelIndex][1] * 100)
        bestCValue = cValues[bestModelIndex]
        bestLogCValue = log10(bestCValue)
        print >> sys.stderr, "C value: ", bestCValue
        print >> sys.stderr, "log10(C) value: ", bestLogCValue
        
        # Keep the best model as the final predictor, so it can be saved to disk
        self.estimator = estimators[bestModelIndex]
        self.estimator.fit(self.X[:,self.activeColumnIndices],self.y)

        return (scoreList[bestModelIndex])

    def predict(self, X):
        assert(type(X) == type(pd.DataFrame()))
        X_scaled = self.scaler.transform(X.astype(float))
        return self.estimator.predict(X_scaled[:,self.activeColumnIndices])

    def predict_proba(self, X):
        assert(type(X) == type(pd.DataFrame()))
        X_scaled = self.scaler.transform(X.astype(float))
        return self.estimator.predict_proba(X_scaled[:,self.activeColumnIndices])

    def getCoefficients(self):
        # There is only one class to predict, so we return the first element only
        return self.estimator.coef_[0]

    def saveToDisk(self, pathToFile='/tmp/kivaLoanFundingPredictor.pkl'):
        toBePickled = (self.estimator, self.scaler, self.columns, self.activeColumnIndices)
        pickle.dump(toBePickled, open(pathToFile,"wb"))

    def loadFromDisk(self, pathToFile='/tmp/kivaLoanFundingPredictor.pkl'):
        (self.estimator, self.scaler, self.columns, self.activeColumnIndices) = pickle.load(open(pathToFile, "rb"))

if __name__ == "__main__":
    
    print >> sys.stderr, "Creating KivaPartner objects via Kiva Web API ...",
    kivaPartners = KivaPartners()
    print >> sys.stderr, "done"

    kivaToyLoanIdCollection = [376222,
                               376200,
                               379441,
                               379445,
                               378854,
                               379446,
                               379447,
                               379449,
                               379448,
                               379450,
                               379451]
    
    print >> sys.stderr, "Creating KivaLoan objects via Kiva Web API ...",
    kivaToyLoanCollection = KivaLoans(loanIdList=kivaToyLoanIdCollection)
    print >> sys.stderr, "done"
    print >> sys.stderr, "kivaToyLoanCollection = ", kivaToyLoanCollection
    
    print >> sys.stderr, "Getting ground truth labels ...",
    groundTruthLabels = kivaToyLoanCollection.getLabels()
    print >> sys.stderr, "done"
    print >> sys.stderr, "groundTruthLabels = ", groundTruthLabels

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

    print >> sys.stderr, "Getting all features at once ..."
    settingsFile = "%s/%s" % (projectDir, 'data/predicting_funding/slda_settings.txt')    
    columns, allFeatures = kivaToyLoanCollection.getAllFeatures(slda, settingsFile, transformCategorical=True)
    print >> sys.stderr, "done"
   
    # Preparing dataframe
    trainDF = pd.DataFrame.from_items(zip(kivaToyLoanIdCollection, allFeatures), columns=columns, orient='index')

    print >> sys.stderr, "columns = ", columns
    print >> sys.stderr, 'trainDF.head(3) = ', trainDF.head(3)

    predictor = KivaLoanFundingPredictor()
    predictor.feedDataFrames(X=trainDF, y=groundTruthLabels)

    predictor.trainAndEvaluate(nrCrossValidationFolds=2)

#    predictor.train()

    predictor.saveToDisk()

    unseenKivaLoans = [847571, 847570, 848289]
    unseenKivaLoanCollection = KivaLoans(unseenKivaLoans)

    columns2, unseenFeatures = unseenKivaLoanCollection.getAllFeatures(slda, settingsFile, transformCategorical=True)
    assert(columns == columns2)

    unseenDF = pd.DataFrame.from_items(zip(unseenKivaLoans, unseenFeatures), columns=columns, orient='index')

    predictor.loadFromDisk()

    # With all columns active
    print "Active columns = ", predictor.getActiveColumns()
    probaList = predictor.predict_proba(X=unseenDF)
    predictions = predictor.predict(X=unseenDF)

    print >> sys.stderr, "probaList = ", probaList
    print >> sys.stderr, "predictions = ", predictions

    # With only some columns active
    predictor.setActiveColumns(['MajorityGender'])
    predictor.trainAndEvaluate(nrCrossValidationFolds=2)

    print "Active columns = ", predictor.getActiveColumns()
    probaList = predictor.predict_proba(X=unseenDF)
    predictions = predictor.predict(X=unseenDF)

    print >> sys.stderr, "probaList = ", probaList
    print >> sys.stderr, "predictions = ", predictions

