from pymongo import MongoClient
from datetime import datetime
from nltk import sent_tokenize, word_tokenize
from gensim.corpora import Dictionary, BleiCorpus, dictionary
import codecs
import os
import sys

client = MongoClient()

nrDocs = 1000
langCode = "en"
loansCollection = client.kiva.loans
#print "Number of loan descriptions in '%s': %d" % (langCode,loansCollection.find({"processed_description.texts.%s" % langCode :{'$exists': True}}).count())

startYear = 2015
start = datetime(startYear, 1, 1)
c = loansCollection.find({"$and" : [{"posted_date" : { "$gte" : start }},
                                    {"processed_description.texts.%s" % langCode :{'$exists': True}}
                                    ]
                          })

print "Number of loans in '%s' since %d: %d" % (langCode,startYear,c.count())

id2word= Dictionary([])

# Heavily inspired by https://radimrehurek.com/gensim/tut1.html
class MyCorpus(object):
    def __init__(self, dict=None, cursor=None, firstNrDocs=-1, langCode='en'):
        self.cursor = cursor
        self.firstNrDocs = firstNrDocs
        self.langCode = langCode
        self.dict = dict

    def __iter__(self):
        for loan in self.cursor[:nrDocs]:
            rawDoc = loan["processed_description"]["texts"][self.langCode]
            sentences = sent_tokenize(rawDoc)
            words = [word_tokenize(s) for s in sentences]
#            print words
            flat = [val for sentence in words for val in sentence]
#            print flat
            yield self.dict.doc2bow(flat,allow_update=True)
                        
streamedCorpus = MyCorpus(id2word, c, nrDocs, langCode)
print >> sys.stderr, "First pass: stream in the MongoDB data ...",
for c in streamedCorpus:
    pass

# Save dictionary on disk in binary format
dictionaryBinaryFile = "data/topicmodelling/kiva_dict.bin"
dictionaryTextFile = "data/topicmodelling/kiva_dict.txt"
print >> sys.stderr, "saving into %s ..." % dictionaryBinaryFile,
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
print >> sys.stderr, "Second pass: stream in the MongoDB data ...",
c = loansCollection.find({"$and" : [{"posted_date" : { "$gte" : start }},
                                    {"processed_description.texts.%s" % langCode :{'$exists': True}}
                                    ]
                          })

print >> sys.stderr, "saving into %s (Blei corpus format) ..." % corpusFile,
BleiCorpus.serialize(corpusFile, MyCorpus(id2word, c, nrDocs, langCode), id2word=id2word)
print >> sys.stderr, "done"
