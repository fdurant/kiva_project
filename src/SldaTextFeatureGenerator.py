import os
import subprocess
import sys
import csv
import re
from pprint import pprint
from random import random
from time import sleep
from gensim.corpora import Dictionary
from nltk import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from KivaLoan import KivaLoan

class SldaTextFeatureGenerator(object):
    ''' Class representing a predictor loaded with a pre-trained sLDA model,
    that generates features ("gammas") for unseen documents '''

    def __init__(self, modelFileBin=None, modelFileTxt=None, dictionaryFile=None, vocabFile=None, nrWordsPerTopic=10, sldaBin='slda'):
        self.modelFileBin=modelFileBin
        self.modelFileTxt=modelFileTxt
        self.vocabFile=vocabFile
        self.nrWordsPerTopic=nrWordsPerTopic
        self.sldaBin=sldaBin
        self.gensimDictionary = Dictionary.load_from_text(dictionaryFile)
        self.vocab = []
        with open(self.vocabFile, 'rb') as tsvfile:
            vocabReader = csv.reader(tsvfile, delimiter='\t')
            for row in vocabReader:
                self.vocab.append(row[0])
        
        self.topics = []
        modelFileHandle = open(modelFileTxt, "rb")
        # Discard first 5 lines
        _ = modelFileHandle.readline()
        self.nrTopics = int(re.match("number of topics: (\d+)",modelFileHandle.readline()).group(1))
        _ = modelFileHandle.readline()
        _ = modelFileHandle.readline()
        _ = modelFileHandle.readline()

        for t in range(self.nrTopics):
            betas = [float(beta) for beta in re.split("\s+",modelFileHandle.readline()) if beta != ""]

            sortedBetaIndices = sorted(range(len(betas)), key=lambda k: betas[k], reverse=True)
            assert(len(sortedBetaIndices) == len(self.vocab))

            self.topics.append([(self.vocab[i],betas[i]) for i in sortedBetaIndices[0:self.nrWordsPerTopic]])
            
        _ = modelFileHandle.readline()
        self.etas = [float(eta) for eta in re.split("\s+",modelFileHandle.readline()) if eta != ""]
        assert(len(self.etas) == self.nrTopics)

    def getGensimDictionary(self):
        return self.gensimDictionary
    
    def getVocab(self):
        return self.vocab
    
    def doTestRun(self):
        return subprocess.check_output(self.sldaBin)

    def getTopics(self, nrWordsPerTopic=10, sortedByDescendingEta=False, withEtas=True, withBetas=False):
        assert(nrWordsPerTopic <= self.nrWordsPerTopic)

        result = []

        if sortedByDescendingEta:
            etaIndices = sorted(range(len(self.etas)), key=lambda k: self.etas[k], reverse=False)
        else:
            etaIndices = range(len(self.etas))

        for t in etaIndices:
            eta = self.etas[t]
            topic = self.topics[t] if withBetas else [top[0] for top in self.topics[t]]
            if withEtas:
                result.append((eta, topic[0:nrWordsPerTopic]))
            else:
                result.append(topic[0:nrWordsPerTopic])
            
        return result

    def getNrTopics(self):
        return self.nrTopics

    def getGammasFromDataFile(self, dataFile=None, labelFile=None, settingsFile=None, outDir='/tmp', sortedByDescendingEta=False):
        ''' Inference step: for a dataFile containing test instances,
        for which we *possibly* have a labelFile too, the sLDA model
        transforms each instance into a vector of gamma values (one gamma per topic).
        The order of the gamma values for each instance can be the original order,
        or from large to low eta '''

        # If no labelFile is given, we need to create (a fake one) ourselves, just for the sake of sLDA
        removeLabelFileLaterOn = False
        if labelFile is None:
            removeLabelFileLaterOn = True
            labelFile = "%s/%s_%s.dat" % (outDir,'dummy_label_file_with_random_contents', os.getpid())
            labelFH = open(labelFile, 'wb')
            dataFH = open(dataFile, 'rb')
            for line in dataFH:
                # Fake values, 0 or 1 (at random)
                labelFH.write("%d\n" % round(random()))
            labelFH.close()
            
        output = subprocess.check_output([self.sldaBin, 'inf', dataFile, labelFile, settingsFile, self.modelFileBin, outDir])

        # Collect the gammas from outdir
        outputGammaFile = "%s/%s" % (outDir, 'inf-gamma.dat')
        outputGammaFileHandle = open(outputGammaFile, 'rb')
        gammas = []

        if sortedByDescendingEta:
            etaIndices = sorted(range(len(self.etas)), key=lambda k: self.etas[k], reverse=False)
        else:
            etaIndices = range(len(self.etas))

        for line in outputGammaFileHandle:
            unsortedGammas = re.split("\s+",line.rstrip('\n'))
            gammasThisLine = []
            for t in etaIndices:
                gammasThisLine.append(float(unsortedGammas[t]))
            gammas.append(gammasThisLine)

        if removeLabelFileLaterOn:
            os.remove(labelFile)

        return gammas

    def getGammasFromDescriptions(self, descriptionList=None, settingsFile=None, outDir='/tmp', sortedByDescendingEta=False):
        ''' Same as getGammesFromDataFile, except that we first need to produce the file from raw documents '''
        assert(len(descriptionList) > 0)
        
        bowList = []
        # First we need to convert each description in a Bag-Of-Words representation, and save that as a DataFile
        tmpDataFile = "%s/%s_%s.dat" % (outDir,'temporary_data_file', os.getpid())
        tmpDataFH = open(tmpDataFile, 'wb')
        for desc in descriptionList:
            sentences = sent_tokenize(desc)
            words = [word_tokenize(s) for s in sentences]
            flat = [val.lower() for sentence in words for val in sentence]
            bow = self.gensimDictionary.doc2bow(flat,allow_update=False)
            tmpDataFH.write("%d " % len(bow))
            tmpDataFH.write(" ".join(["%d:%d" % (w[0],w[1]) for w in bow]))
            tmpDataFH.write("\n")
        tmpDataFH.close()

        result = self.getGammasFromDataFile(dataFile=tmpDataFile, 
                                            labelFile=None, 
                                            settingsFile=settingsFile,
                                            outDir=outDir, 
                                            sortedByDescendingEta=sortedByDescendingEta)

        os.remove(tmpDataFile)
        return result

if __name__ == "__main__":

    from os.path import expanduser
    homeDir = expanduser("~")
    projectDir = "%s/%s" % (homeDir, 'work/metis_projects/passion_project/kiva_project')
    sldaBin = "%s/%s" % (homeDir, 'install/slda-master/slda')
    modelFileBin = "%s/%s" % (projectDir, 'data/predicting_funding/slda_out/final.model')
    modelFileTxt = "%s/%s" % (projectDir, 'data/predicting_funding/slda_out/final.model.text')
    dictionaryFile = "%s/%s" % (projectDir, 'data/predicting_funding/kiva_dict.txt')
    vocabFile = "%s/%s" % (projectDir, 'data/predicting_funding/kiva.lda-c.vocab')

    slda1 = SldaTextFeatureGenerator(modelFileBin=modelFileBin,
                                     modelFileTxt=modelFileTxt,
                                     dictionaryFile=dictionaryFile,
                                     vocabFile=vocabFile,
                                     sldaBin=sldaBin)

    dict1 = slda1.getGensimDictionary()
    vocab1 = slda1.getVocab()
    assert(len(dict1.values()) == len(vocab1))

    assert("usage" in slda1.doTestRun())

    assert(slda1.getNrTopics() == 20)
    topics1a = slda1.getTopics(nrWordsPerTopic=2, sortedByDescendingEta=True, withEtas=True, withBetas=True)
    assert(len(topics1a) == 20)

    dataFile1 = "%s/%s" % (projectDir, 'data/predicting_funding/slda_in/kiva-test-data.dat')
    settingsFile1 = "%s/%s" % (projectDir, 'data/predicting_funding/slda_settings.txt')
    labelFile1 = "%s/%s" % (projectDir, 'data/predicting_funding/slda_in/kiva-test-label.dat')
    
    gammas1a = slda1.getGammasFromDataFile(dataFile=dataFile1, 
                                           labelFile=labelFile1, 
                                           settingsFile=settingsFile1,
                                           outDir='/tmp',
                                           sortedByDescendingEta=False)[0]
    
    gammas1b = slda1.getGammasFromDataFile(dataFile=dataFile1, labelFile=labelFile1, 
                                           settingsFile=settingsFile1,
                                           outDir='/tmp',
                                           sortedByDescendingEta=True)[0]
    
    # Different order, but same contents
    assert(len(gammas1a) > 0)
    assert(len(set(gammas1a) - set(gammas1b)) == 0)

    # Without label file
    gammas1c = slda1.getGammasFromDataFile(dataFile=dataFile1, 
                                           settingsFile=settingsFile1,
                                           outDir='/tmp',
                                           sortedByDescendingEta=False)[0]
    assert(len(gammas1c) > 0)

    kivaLoan1 = KivaLoan(id=844974)
    desc1 = kivaLoan1.getEnglishDescription()
#    desc1 = "Yaqout lives in Al Hashmiya. Her father is employed in Saudi Arabia but his income does not cover all of the familys needs.\r\n\r\nShe has decided to study political management and seek work in this field. She is tired of the political and security situation in the world these days and wants to help find solutions for it. \r\n\r\nHer familys financial difficulty means they cannot cover all her university fees. Yaqout has applied for a loan to help pay her semester fees and achieve her dreams."
    descriptionList = [desc1]
    sortedByDescendingEta1b = False
    gammas1d =  slda1.getGammasFromDescriptions(descriptionList,
                                                settingsFile=settingsFile1,
                                                outDir='/tmp',
                                                sortedByDescendingEta=sortedByDescendingEta1b)[0]

    topics1d = slda1.getTopics(nrWordsPerTopic=5, sortedByDescendingEta=sortedByDescendingEta1b, withEtas=False, withBetas=False)
    # Order the topics by most prominent to least prominent
#    for entry in sorted(zip(topics1d,gammas1d), key=lambda x:x[1], reverse=True):
#        print entry

