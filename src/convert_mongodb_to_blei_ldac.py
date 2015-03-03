from pymongo import MongoClient
from datetime import datetime
from nltk import sent_tokenize, word_tokenize
from gensim.corpora import Dictionary, BleiCorpus, dictionary
import codecs
import os
import sys

client = MongoClient()

maxNrDocs = 50000
langCode = "en"
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

id2word=Dictionary([])

# Heavily inspired by https://radimrehurek.com/gensim/tut1.html
class MyCorpus(object):
    def __init__(self, dict=None, cursor=None, firstNrDocs=-1, langCode='en'):
        self.cursor = cursor
        self.firstNrDocs = firstNrDocs
        self.langCode = langCode
        self.dict = dict

    def __iter__(self):
        for loan in self.cursor[:maxNrDocs]:
            rawDoc = loan["processed_description"]["texts"][self.langCode]
            sentences = sent_tokenize(rawDoc)
            words = [word_tokenize(s) for s in sentences]
#            print words
            flat = [val for sentence in words for val in sentence]
#            print flat
            yield self.dict.doc2bow(flat,allow_update=True)
                        
streamedCorpus = MyCorpus(id2word, c, maxNrDocs, langCode)
print >> sys.stderr, "First pass: streaming from MongoDB ..."

# By iterating over streamedCorpus, we actually stream in data and populate id2word
realNrDocs = 0
for i,c in enumerate(streamedCorpus): 
    if i % 5000 == 0 and i != 0:
        print >> sys.stderr, "read %d records ..." % i
    realNrDocs += 1

# Save dictionary on disk in binary format
dictionaryBinaryFile = "data/topicmodelling/kiva_dict.bin"
dictionaryTextFile = "data/topicmodelling/kiva_dict.txt"
print >> sys.stderr, "wrote %s ..." % dictionaryBinaryFile,
dictionaryDir = os.path.dirname(dictionaryBinaryFile)
try:
    os.stat(dictionaryDir)
except:
    os.mkdir(dictionaryDir)

id2word.save(dictionaryBinaryFile)
print >> sys.stderr, "and %s ..." % dictionaryTextFile,
id2word.save_as_text(dictionaryTextFile)
print >> sys.stderr, "done"

# Save corpus on disk
corpusFile = "data/topicmodelling/kiva.lda-c"
corpusDir = os.path.dirname(corpusFile)
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
BleiCorpus.serialize(corpusFile, MyCorpus(id2word, c, maxNrDocs, langCode), id2word=id2word)
print >> sys.stderr, "done"
print >> sys.stderr, "Number of documents converted: %d" % realNrDocs
print >> sys.stderr, "Vocabulary size: %d" % len(id2word.keys())
