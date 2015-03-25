import argparse
import sys
import csv
import re

parser = argparse.ArgumentParser()
parser.add_argument('--vocabFile', help='Vocabulary file in Blei format, one word per line', required=True)
parser.add_argument('--sldaModelFile', help='Trained sLDA model file', required=True)
parser.add_argument('--nrWordsPerTopic', help='Number of most salient words to print out per topic', default=10)
args = parser.parse_args()

nrWordsPerTopic = int(args.nrWordsPerTopic)

vocab = []
print >> sys.stderr, "Loading vocabulary from %s ..." % args.vocabFile,
with open(args.vocabFile, 'rb') as tsvfile:
    vocabReader = csv.reader(tsvfile, delimiter='\t')
    for row in vocabReader:
        vocab.append(row[0])
print >> sys.stderr, "done"

topics = []
modelFileHandle = open(args.sldaModelFile, "rb")
# Discard first 5 lines
_ = modelFileHandle.readline()
nrTopics = int(re.match("number of topics: (\d+)",modelFileHandle.readline()).group(1))
_ = modelFileHandle.readline()
_ = modelFileHandle.readline()
_ = modelFileHandle.readline()

topics = []
for t in range(nrTopics):
    betas = [float(beta) for beta in re.split("\s+",modelFileHandle.readline()) if beta != ""]
#    print "len(betas) =", len(betas)

    sortedBetaIndices = sorted(range(len(betas)), key=lambda k: betas[k], reverse=True)
    assert(len(sortedBetaIndices) == len(vocab))

    topics.append([vocab[i] for i in sortedBetaIndices[0:nrWordsPerTopic]])

# Now sort the topics by their eta value, from negative to positive
_ = modelFileHandle.readline()
etas = [float(eta) for eta in re.split("\s+",modelFileHandle.readline()) if eta != ""]
assert(len(etas) == nrTopics)
sortedEtaIndices = sorted(range(len(etas)), key=lambda k: etas[k], reverse=False)

print "ETA     TOPIC"
for t in sortedEtaIndices:
    eta = etas[t]
    print "%+.2f : [" % eta,
    print " ".join(topics[t]),
    print "]"
