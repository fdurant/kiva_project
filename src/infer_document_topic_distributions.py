from pymongo import MongoClient
from gensim import corpora, models
from gensim.models.ldamodel import LdaModel
from pandas.io.pytables import read_hdf
import sys
from pprint import pprint
import numpy as np
import pickle

import argparse

def parseArguments():

    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--modelDir', help='Directory for reading the LDA model', required=True)
    parser.add_argument('--modelBaseName', help='Base name for the model and corpus', required=True)
    parser.add_argument('--maxNrDocs', help='Maximum number of documents to process', default=1000000)
    args = parser.parse_args()

def readTopicWordsMatrix():

    global topicsWordsMatrix
    topicWordsMatrixFile = "%s/%s_topic_words_matrix.h5" % (args.modelDir, args.modelBaseName)
    print >> sys.stderr, "Reading topic/word matrix file %s ..." % topicWordsMatrixFile,
    topicsWordsMatrix = read_hdf(topicWordsMatrixFile, 'table')
    print >> sys.stderr, "done"

#    print topicsWordsMatrix

def loadLDAModelFile():

    global topicsAsWeightedWordVectors
    global ldaModel
    modelFile = "%s/%s.lda_model" % (args.modelDir, args.modelBaseName)
    modelDir = args.modelDir
    print >> sys.stderr, "Loading model file %s ..." % modelFile,
    ldaModel = LdaModel.load(modelFile)
    print >> sys.stderr, "done"
    topicsAsWeightedWordVectors = ldaModel.show_topics(num_topics=topicsWordsMatrix.shape[0],num_words=8,formatted=False)
#    print "topicsAsWeightedWordVectors = "
#    pprint(topicsAsWeightedWordVectors)

def readBleiCorpus():

    global corpus
    corpusFile = "%s/%s.lda-c" % (args.modelDir, args.modelBaseName)
    vocabFile = "%s/%s.lda-c.vocab" % (args.modelDir, args.modelBaseName)

    print >> sys.stderr, "Loading Blei corpus file %s ..." % corpusFile,
    corpus = corpora.BleiCorpus(corpusFile, fname_vocab=vocabFile)
    print >> sys.stderr, "done"

    print corpus

def processDocuments():
    
    global docsPerTopic
    global topicDistributionsAllDocs
    topicDistributionsAllDocs = np.ndarray(shape=(1,len(topicsAsWeightedWordVectors)), dtype=float)
    winningTopic = [0.0 for topic in range(len(topicsAsWeightedWordVectors))]

    totalNrDocs = 0

    for i, doc in enumerate(corpus[:]):
        totalNrDocs += 1
        if i % 5000 == 0 and i > 0:
            print "Processed %d documents ..." % i
        (gamma, _) = ldaModel.inference([doc])
#        print "type(gamma) = ", type(gamma)
#        print "gamma.shape = ", gamma.shape
#        print "gamma = ", gamma
        indexMax=gamma.argmax()
#        print "indexMax = ", indexMax
        winningTopic[indexMax] += 1
        topicDistributionsAllDocs += gamma   

    totalMass = topicDistributionsAllDocs.sum()

    for topicId in range(len(topicsAsWeightedWordVectors)):
        print "%d winning (%1.2f%%); %1.2f%% weight in %s" % (winningTopic[topicId], 
                                                              (float(winningTopic[topicId])/totalNrDocs)*100,
                                                              (topicDistributionsAllDocs[0,topicId]/totalMass)*100,
                                                              " ".join([t[1] for t in topicsAsWeightedWordVectors[topicId]]))

def saveInferredDistributions():
    
    topicDistributionsFile = "%s/%s_topic_distributions.p" % (args.modelDir, args.modelBaseName)
    with open(topicDistributionsFile, 'wb') as pickleFile:
        pickle.dump(topicDistributionsAllDocs, pickleFile)

if __name__ == "__main__":
    parseArguments()

    readTopicWordsMatrix()

    loadLDAModelFile()

    readBleiCorpus()

    processDocuments()

    saveInferredDistributions()
