from gensim import corpora, models
from gensim.models.ldamodel import LdaModel
from gensim.models.tfidfmodel import TfidfModel
import sys
import argparse
import os
import pandas as pd
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--dataDir', help='Directory for reading the corpus and vocabulary data', required=True)
parser.add_argument('--modelDir', help='Directory for writing the LDA model', required=True)
parser.add_argument('--corpusBaseName', help='Base name for the corpus', required=True)
parser.add_argument('--nrTopics', help='Number of topics to be estimated', default=10)
parser.add_argument('--nrWords', help='Number of words to show per topic', default=10)
args = parser.parse_args()

corpusFile = "%s/%s.lda-c" % (args.dataDir, args.corpusBaseName)
vocabFile = "%s/%s.lda-c.vocab" % (args.dataDir, args.corpusBaseName)

print >> sys.stderr, "Loading Blei corpus file %s ..." % corpusFile,
corpus = corpora.BleiCorpus(corpusFile, fname_vocab=vocabFile)
print >> sys.stderr, "done"

print(corpus)

# Read dictionary
dictFileBinary = "%s/%s_dict.bin" % (args.dataDir, args.corpusBaseName)
id2word = corpora.Dictionary.load(dictFileBinary)
print id2word

#corpusTfidf = TfidfModel(corpus, normalize=True)
#print corpusTfidf

nrTopics = int(args.nrTopics)
nrWords = int(args.nrWords)
#ldaModel = LdaModel(corpusTfidf, id2word=id2word, num_topics=nrTopics)
print >> sys.stderr, "Making topic model ...",
ldaModel = LdaModel(corpus, id2word=id2word, num_topics=nrTopics)
print >> sys.stderr, "done"
topicsAsString = ldaModel.show_topics(num_topics=nrTopics,num_words=nrWords)
for t in topicsAsString:
    print t

modelFile = "%s/%s.lda_model" % (args.modelDir, args.corpusBaseName)
modelDir = args.modelDir
try:
    os.stat(modelDir)
except:
    os.mkdir(modelDir)
print >> sys.stderr, "Writing model file %s ..." % modelFile,
ldaModel.save(modelFile)
print >> sys.stderr, "done"

print >> sys.stderr, "Creating complete topic/word matrix in memory:"
# Store *all* words
topicsAsWeightedWordVectors = ldaModel.show_topics(num_topics=nrTopics,num_words=len(id2word.keys()), formatted=False)
#topicsAsWeightedWordVectors = ldaModel.show_topics(num_topics=nrTopics,num_words=nrWords, formatted=False)
words = [w for w in sorted(id2word.values())]
topicsWordsMatrix = pd.DataFrame(0.0, index=range(len(topicsAsWeightedWordVectors)), columns=words)
for i,topic in enumerate(topicsAsWeightedWordVectors):
#    print tuplesList
    print >> sys.stderr, "topic %d/%d ..." % (i+1,len(topicsAsWeightedWordVectors))
    for weight, word in topic:
        topicsWordsMatrix[word][i] = weight
print >> sys.stderr, "done"

#print topicsWordsMatrix

topicWordsMatrixFile = "%s/%s_topic_words_matrix.h5" % (args.modelDir, args.corpusBaseName)
print >> sys.stderr, "Writing topic/word matrix file %s ..." % topicWordsMatrixFile,

# See http://pandas.pydata.org/pandas-docs/dev/io.html#io-hdf5

topicsWordsMatrix.to_hdf(topicWordsMatrixFile, 'table')
print >> sys.stderr, "done"
