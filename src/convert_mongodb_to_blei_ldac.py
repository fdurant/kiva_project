from pymongo import MongoClient
from datetime import datetime
from nltk import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from gensim.corpora import Dictionary, BleiCorpus
import codecs
import os
import sys
import argparse
import csv

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--dataDir', help='Directory for writing the corpus and vocabulary data', required=True)
parser.add_argument('--corpusBaseName', help='Base name for the corpus', required=True)
parser.add_argument('--stopwordFile', help='File with extra corpus-specific stop words', required=False)
parser.add_argument('--maxNrDocs', help='Maximum number of documents to convert', default=1000000)
parser.add_argument('--filterBelow', help='Minimum number of documents in which a vocab word must occur', default=5)
parser.add_argument('--filterAbove', help='Vocab words that appear in more than this PERCENTAGE of docs are filtered', default=0.5)
parser.add_argument('--filterKeepN', help='Number of vocab words to keep after the Below and Above filters have been applied', default=100000)
args = parser.parse_args()

client = MongoClient()

maxNrDocs = int(args.maxNrDocs)
langCode = "en"
langName="english"
loansCollection = client.kiva.loans
#print "Number of loan descriptions in '%s': %d" % (langCode,loansCollection.find({"processed_description.texts.%s" % langCode :{'$exists': True}}).count())

startYear = 2010
start = datetime(startYear, 1, 1)
print >> sys.stderr, "Creating MongoDB cursor ...",
c = loansCollection.find({"$and" : [{"posted_date" : { "$gte" : start }},
                                    {"processed_description.texts.%s" % langCode :{'$exists': True}}
                                    ]
                          })
print >> sys.stderr, "done"
print "Number of loans in '%s' since %d: %d" % (langCode,startYear,c.count())


stopWords = {stopWord:1 for stopWord in stopwords.words('english')}

# Add additional stopwords, if specified
if args.stopwordFile:
    with open(args.stopwordFile, 'rb') as csvfile:
     stopwordReader = csv.reader(csvfile, delimiter="\t")
     for sw in stopwordReader:
         stopWords[unicode(sw[0], 'utf-8')] = 1
#print "stopWords =", stopWords

id2word=Dictionary([])

# Heavily inspired by https://radimrehurek.com/gensim/tut1.html
class MyCorpus(object):
    def __init__(self, dict=None, allowDictUpdate=True, cursor=None, firstNrDocs=-1, langCode='en'):
        self.cursor = cursor
        self.firstNrDocs = firstNrDocs
        self.langCode = langCode
        self.dict = dict
        self.allowDictUpdate = allowDictUpdate

    def __iter__(self):
        for loan in self.cursor[:maxNrDocs]:
            rawDoc = loan["processed_description"]["texts"][self.langCode]
            sentences = sent_tokenize(rawDoc)
            words = [word_tokenize(s) for s in sentences]
#            print words
            flat = [val.lower() for sentence in words for val in sentence if not stopWords.has_key(val.lower())]
#            print flat
            yield self.dict.doc2bow(flat,allow_update=self.allowDictUpdate)
                        
streamedCorpus = MyCorpus(id2word, True, c, maxNrDocs, langCode)
print >> sys.stderr, "First pass: streaming from MongoDB ..."

print >> sys.stderr, "creating the dictionary ..."
# By iterating over streamedCorpus, we actually stream in data and populate id2word
realNrDocs = 0
for i,c in enumerate(streamedCorpus): 
    if i % 5000 == 0 and i != 0:
        print >> sys.stderr, "read %d documents ..." % i
    realNrDocs += 1

# Filter out unwanted vocabulary items
print >> sys.stderr, "filtering the dictionary ...",
id2word.filter_extremes(no_below=int(args.filterBelow), no_above=float(args.filterAbove), keep_n=int(args.filterKeepN))
print >> sys.stderr, "done"

# Save dictionary on disk in binary format
dictionaryBinaryFile = "%s/%s_dict.bin" % (args.dataDir, args.corpusBaseName)
dictionaryTextFile = "%s/%s_dict.txt" % (args.dataDir, args.corpusBaseName)
print >> sys.stderr, "wrote %s ..." % dictionaryBinaryFile,
dictionaryDir = args.dataDir
try:
    os.stat(dictionaryDir)
except:
    os.mkdir(dictionaryDir)

id2word.save(dictionaryBinaryFile)
print >> sys.stderr, "and %s ..." % dictionaryTextFile,
id2word.save_as_text(dictionaryTextFile)
print >> sys.stderr, "done"

# Save corpus on disk
corpusFile = "%s/%s.lda-c" % (args.dataDir, args.corpusBaseName)
corpusDir = args.dataDir
try:
    os.stat(corpusDir)
except:
    os.mkdir(corpusDir)

# Second pass, because we need to *stream* the data into the BleiCorpus format
print >> sys.stderr, "Second pass: streaming from MongoDB ...",
c = loansCollection.find({"$and" : [{"posted_date" : { "$gte" : start }},
                                    {"processed_description.texts.%s" % langCode :{'$exists': True}}
                                    ]
                          })

print >> sys.stderr, "saving into %s (Blei corpus format) ..." % corpusFile,
BleiCorpus.serialize(corpusFile, MyCorpus(id2word, False, c, maxNrDocs, langCode), id2word=id2word)
print >> sys.stderr, "done"
print >> sys.stderr, "Number of documents converted: %d" % realNrDocs
print >> sys.stderr, "Vocabulary size: %d" % len(id2word.items())
