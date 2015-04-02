from KivaLoan import KivaLoan
from KivaPartners import KivaPartners
from os.path import expanduser
from SldaTextFeatureGenerator import SldaTextFeatureGenerator

class KivaLoans(object):
    ''' Class representing a collection of loans at kiva.org '''

    def __init__(self, loanIdList=None, loanDictList=None):
        self.list = []
        self.dict = {}

        if loanIdList:
            for loanId in loanIdList:
                loan = KivaLoan(id=loanId)
                self.list.append(loan)
                self.dict[loan.getId()] = loan

        elif loanDictList:
            for loanDict in loanDictList:
                loan = KivaLoan(dict=loanDict)
                self.list.append(loan)
                self.dict[loan.getId()] = loan
                
    def push(self, loan):
        assert(type(loan).__name__ == 'KivaLoan')
        self.list.append(loan)
        self.dict[loan.getId()] = loan

    def getLoans(self):
        return self.list

    def getLoanIds(self):
        return [loan.getId() for loan in self.list]
    
    def getSize(self):
        return len(self.list)

    def getLabels(self):
        return [loan.getFundingRatioLabel() for loan in self.list]

    def getTopicFeatures(self, slda=None, settingsFile=None):
        descriptionList = [loan.getEnglishDescription() for loan in self.list]
        return slda.getGammasFromDescriptions(descriptionList,
                                              settingsFile=settingsFile,
                                              outDir='/tmp',
                                              sortedByDescendingEta=False)
    def getLoanFeatures(self,transformCategorical=False):
        return [loan.getMultipleFeatures(transformCategorical=transformCategorical) for loan in self.list]

    def getPartnerFeatures(self,partners=KivaPartners()):
        return [partners.getMultiplePartnerFeatures(loan.getPartnerId()) for loan in self.list]

    def getAllFeatures(self, slda=None, settingsFile=None, transformCategorical=False):

        allFeatures = []
        topicFeatures = self.getTopicFeatures(slda=slda, settingsFile=settingsFile)
        loanFeatures = self.getLoanFeatures(transformCategorical=transformCategorical)
        partnerFeatures = self.getPartnerFeatures()
        baselineFeature = [[('Baseline',1.0)] for i in range(len(partnerFeatures))]

        columns = []
        columns.extend([f[0] for f in baselineFeature[0]])
        columns.extend([f[0] for f in loanFeatures[0]])
        columns.extend([f[0] for f in topicFeatures[0]])
        columns.extend([f[0] for f in partnerFeatures[0]])

        for i in range(len(self.list)):
            mergedFeatures = []
            mergedFeatures.extend([f[1] for f in baselineFeature[i]])
            mergedFeatures.extend([f[1] for f in loanFeatures[i]])
            mergedFeatures.extend([f[1] for f in topicFeatures[i]])
            mergedFeatures.extend([f[1] for f in partnerFeatures[i]])
            allFeatures.append(mergedFeatures)

        return (columns, allFeatures)

if __name__ == "__main__":
    
    loanIds = [376222,376200]
    loanCollection = KivaLoans(loanIdList=loanIds)

    assert(len(loanCollection.getLabels()) == loanCollection.getSize())
    assert(loanIds == loanCollection.getLoanIds())

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
    
    settingsFile = "%s/%s" % (projectDir, 'data/predicting_funding/slda_settings.txt')
    topicFeatures = loanCollection.getTopicFeatures(slda,settingsFile)
    assert(len(topicFeatures) == loanCollection.getSize())

    loanFeatures = loanCollection.getLoanFeatures()
    assert(len(loanFeatures) == loanCollection.getSize())

    partnerFeatures = loanCollection.getPartnerFeatures()
    assert(len(partnerFeatures) == loanCollection.getSize())

    columns, allFeatures = loanCollection.getAllFeatures(slda, settingsFile)
    print columns
    print allFeatures
    assert(len(columns) == len(allFeatures[0]))
