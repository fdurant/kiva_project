import argparse
import csv
import numpy as np
import sys
from sklearn.cross_validation import ShuffleSplit
import re

parser = argparse.ArgumentParser()
parser.add_argument('--bleiCorpusFile', help='(INPUT) Original corpus file in Blei format, not split in train/test', required=True)
parser.add_argument('--bleiLabelFile', help='(INPUT) Original label file in Blei format, not split in train/test', required=True)
parser.add_argument('--bleiTrainCorpusFile', help='(OUTPUT) Train corpus file in Blei format', required=True)
parser.add_argument('--bleiTrainLabelFile', help='(OUTPUT) Train label file in Blei format', required=True)
parser.add_argument('--bleiTrainIdFile', help='(OUTPUT) File with loan IDs for training instances, one per line', required=True)
parser.add_argument('--bleiTestCorpusFile', help='(OUTPUT) Test corpus file in Blei format', required=True)
parser.add_argument('--bleiTestLabelFile', help='(OUTPUT) Test label file in Blei format', required=True)
parser.add_argument('--bleiTestIdFile', help='(OUTPUT) File with loan IDs for test instances, one per line', required=True)
parser.add_argument('--test_size', help='as in sklearn.cross_validation.StratifiedShuffleSplit', default=0.5)
parser.add_argument('--train_size', help='as in sklearn.cross_validation.StratifiedShuffleSplit', default=None)
args = parser.parse_args()

# Key: class label
# Value: list containing all indices from the original instance file that have that label
instanceIndicesPerLabel = {}
# First pass: read in the original file with labels, and keep them separate per class
print >> sys.stderr, "Reading original labels from %s ..." % args.bleiLabelFile,
with open(args.bleiLabelFile, 'rb') as tsvfile:
    labelReader = csv.reader(tsvfile, delimiter='\t')
    for i,row in enumerate(labelReader):
        label = int(row[0])
        loanId = row[1]
        # Discard all -1 labels: they represent the "demilitarized" zone between 0 and 1 we don't want to model
        if label < 0:
            continue
        if instanceIndicesPerLabel.has_key(label):
            instanceIndicesPerLabel[label].append((i,loanId))
        else:
            instanceIndicesPerLabel[label] = [(i,loanId)]
print >> sys.stderr, "done"

nrClasses = len(instanceIndicesPerLabel.keys())

smallestClassLength = 0
for l in instanceIndicesPerLabel:
    print >> sys.stderr, "number of original instances in class %d: %d" % (l, len(instanceIndicesPerLabel[l]))
    if smallestClassLength < len(instanceIndicesPerLabel[l]):
        smallestClassLength = len(instanceIndicesPerLabel[l])

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

if type(testSize) == type(1) and type(trainSize) == type(1):
    assert((testSize + trainSize) / nrClasses <= smallestClassLength), "Sum of testSize %d and trainSize %d divided by number of classes %d must be smaller than or equal to smallest class length %d" % (testSize, trainSize, nrClasses, smallestClassLength)
    trainSizePerClass = trainSize/nrClasses
    testSizePerClass = testSize/nrClasses
elif (type(testSize) == type(1.0) and type(trainSize) == type(1.0)):
    # Ratio has been specified
    trainSizePerClass = int(smallestClassLength * trainSize)
    testSizePerClass = int(smallesClassLength * testSize)
elif testSize is None or trainSize is None:
    trainSizePerClass = int(smallestClassLength * 0.5)
    testSizePerClass = int(smallesClassLength * 0.5)

print >> sys.stderr, "trainSizePerClass = ", trainSizePerClass
print >> sys.stderr, "testSizePerClass = ", testSizePerClass

# Key: originalIndex
# Value: associative array with
#        key: metaIndex into instanceIndicesPerLabel[classLabel]
#        value: tuple consisting of:
#               classLabel (in range 0..nrClasses-1)
#               'train' or 'test'
#               id of the original loan
indicesToKeep = {}

for classLabel in sorted(instanceIndicesPerLabel.keys()):
    
    i = 0
    for trainIndex, testIndex in ShuffleSplit(n=len(instanceIndicesPerLabel[classLabel]), 
                                              n_iter=1, 
                                              test_size=testSizePerClass, 
                                              train_size=trainSizePerClass,
                                              random_state=1):
        # We only expect 1 loop
        assert(i == 0)
        i += 1
        print >> sys.stderr, "number of indices of class %d into training set: %d " % (classLabel, len(trainIndex))
        #print >> sys.stderr, "trainIndex[0:10] = ", trainIndex.tolist()[0:10]
        print >> sys.stderr, "number of indices of class %d into test set: %d " % (classLabel, len(testIndex))
        #print >> sys.stderr, "testIndex[0:10] = ", testIndex.tolist()[0:10]

        for m in trainIndex.tolist():
            origIndex, loanId = instanceIndicesPerLabel[classLabel][m]
            assert(indicesToKeep.has_key(origIndex) == False)
            indicesToKeep[origIndex] = (classLabel, 'train', loanId)

        for n in testIndex.tolist():
            origIndex, loanId = instanceIndicesPerLabel[classLabel][n]
            # There should be no overlap between test and training set
            assert(indicesToKeep.has_key(origIndex) == False)
            indicesToKeep[origIndex] = (classLabel, 'test', loanId)

# Now that we know all the indices, create the output files
trainCorpusFileHandle = open(args.bleiTrainCorpusFile, "w")
trainLabelFileHandle = open(args.bleiTrainLabelFile, "w")
trainIdFileHandle = open(args.bleiTrainIdFile, "w")

testCorpusFileHandle = open(args.bleiTestCorpusFile, "w")
testLabelFileHandle = open(args.bleiTestLabelFile, "w")
testIdFileHandle = open(args.bleiTestIdFile, "w")

# Loop over the original Blei corpus file, and assign the instances (and their corresponding labels) to
# the correct output files, according to the train/test index information in indicesToKeep

lineCounter = 0
corpusFile = open(args.bleiCorpusFile, 'r')
for line in corpusFile.readlines():
    if (indicesToKeep.has_key(lineCounter)):
        if indicesToKeep[lineCounter][1] == 'train':
            trainCorpusFileHandle.write(line)
            trainLabelFileHandle.write("%s\n" % indicesToKeep[lineCounter][0])
            trainIdFileHandle.write("%s\n" % indicesToKeep[lineCounter][2])
        elif indicesToKeep[lineCounter][1] == 'test':
            testCorpusFileHandle.write(line)
            testLabelFileHandle.write("%s\n" % indicesToKeep[lineCounter][0])
            testIdFileHandle.write("%s\n" % indicesToKeep[lineCounter][2])
    lineCounter += 1

trainCorpusFileHandle.close()
trainLabelFileHandle.close()

testCorpusFileHandle.close()
testLabelFileHandle.close()
