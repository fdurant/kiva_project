from gensim import corpora, models
from gensim.models.ldamodel import LdaModel
from gensim.models.tfidfmodel import TfidfModel
import sys
import argparse
import os

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
topics = ldaModel.show_topics(num_topics=nrTopics,num_words=nrWords)
for t in topics:
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
