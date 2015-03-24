import argparse
import csv
import numpy as np
import sys
from sklearn.cross_validation import StratifiedShuffleSplit
import re

parser = argparse.ArgumentParser()
parser.add_argument('--bleiCorpusFile', help='(INPUT) Original corpus file in Blei format, not split in train/test', required=True)
parser.add_argument('--bleiLabelFile', help='(INPUT) Original label file in Blei format, not split in train/test', required=True)
parser.add_argument('--bleiTrainCorpusFile', help='(OUTPUT) Train corpus file in Blei format', required=True)
parser.add_argument('--bleiTrainLabelFile', help='(OUTPUT) Train label file in Blei format', required=True)
parser.add_argument('--bleiTestCorpusFile', help='(OUTPUT) Test corpus file in Blei format', required=True)
parser.add_argument('--bleiTestLabelFile', help='(OUTPUT) Test label file in Blei format', required=True)
parser.add_argument('--test_size', help='as in sklearn.cross_validation.StratifiedShuffleSplit', default=0.5)
parser.add_argument('--train_size', help='as in sklearn.cross_validation.StratifiedShuffleSplit', default=None)
args = parser.parse_args()

labels = []
# First pass: read in the original file with labels
print >> sys.stderr, "Reading original labels from %s ..." % args.bleiLabelFile,
with open(args.bleiLabelFile, 'rb') as tsvfile:
    ccReader = csv.reader(tsvfile, delimiter='\t')
    for i,row in enumerate(ccReader):
        labels.append(row[0])
print >> sys.stderr, "done"

print >> sys.stderr, "number of labels read: %d" % len(labels)

testSize = None
if not args.test_size is None:
    if re.match("\.", args.test_size):
        testSize = float(args.test_size)
    else:
        testSize = int(args.test_size)

trainSize = None
if not args.train_size is None:
    if re.match("\.", args.train_size):
        trainSize = float(args.train_size)
    else:
        trainSize = int(args.train_size)

# Inspired by http://scikit-learn.org/stable/modules/generated/sklearn.cross_validation.StratifiedShuffleSplit.html#sklearn.cross_validation.StratifiedShuffleSplit

# Value: index (in range 0 .. len(labels))
# Key: 'train' or 'test'
indicesToKeep = {}

i = 0
for trainIndex, testIndex in StratifiedShuffleSplit(labels, 1, test_size=testSize, train_size=trainSize, random_state=1):
    # We only expect 1 loop
    assert(i == 0)
    i += 1
    print >> sys.stderr, "number of indices into training set: %d " % len(trainIndex)
#    print >> sys.stderr, "trainIndex[0:10] = ", trainIndex.tolist()[0:10]
    print >> sys.stderr, "number of indices into test set: %d " % len(testIndex)
#    print >> sys.stderr, "testIndex[0:10] = ", testIndex.tolist()[0:10]

    for i in trainIndex.tolist():
        assert(indicesToKeep.has_key(i) == False)
        indicesToKeep[i] = 'train'

    for j in testIndex.tolist():
        # There should be no overlap between test and training set
        assert(indicesToKeep.has_key(j) == False)
        indicesToKeep[j] = 'test'

# Now that we know all the indices, create the output files
trainCorpusFileHandle = open(args.bleiTrainCorpusFile, "w")
trainLabelFileHandle = open(args.bleiTrainLabelFile, "w")

testCorpusFileHandle = open(args.bleiTestCorpusFile, "w")
testLabelFileHandle = open(args.bleiTestLabelFile, "w")

# Loop over the original Blei corpus file, and assign the instances (and their corresponding labels) to
# the correct output files, according to the train/test index information in indicesToKeep

lineCounter = 0
corpusFile = open(args.bleiCorpusFile, 'r')
for line in corpusFile.readlines():
    if (indicesToKeep.has_key(lineCounter)):
        if indicesToKeep[lineCounter] == 'train':
            trainCorpusFileHandle.write(line)
            trainLabelFileHandle.write("%s\n" % labels[lineCounter])
        elif indicesToKeep[lineCounter] == 'test':
            testCorpusFileHandle.write(line)
            testLabelFileHandle.write("%s\n" % labels[lineCounter])
    lineCounter += 1

assert(lineCounter == len(labels)), 'Expecting line count %d to be equal to number of labels %d' % (lineCounter, len(labels))

trainCorpusFileHandle.close()
trainLabelFileHandle.close()

testCorpusFileHandle.close()
testLabelFileHandle.close()
