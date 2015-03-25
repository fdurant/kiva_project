from sklearn.metrics import precision_recall_fscore_support
import argparse
import sys
import csv

parser = argparse.ArgumentParser()
parser.add_argument('--predictedFile', help='File with predicted class labels, one line per test instance', required=True)
parser.add_argument('--expectedFile', help='File with expected (= ground truth) class labels, one line per test instance', required=True)
parser.add_argument('--average', help='as used by sklearn.metrics.precision_recall_fscore_support', default=None)
args = parser.parse_args()

predicted = []

print >> sys.stderr, "Reading predicted classes from %s ..." % args.predictedFile,
with open(args.predictedFile, 'rb') as predictedFileHandle:
    predictedReader = csv.reader(predictedFileHandle, delimiter='\t')
    for i,row in enumerate(predictedReader):
        predicted.append(int(row[0]))
print >> sys.stderr, "done"

expected = []

print >> sys.stderr, "Reading expected classes from %s ..." % args.expectedFile,
with open(args.expectedFile, 'rb') as expectedFileHandle:
    expectedReader = csv.reader(expectedFileHandle, delimiter='\t')
    for i,row in enumerate(expectedReader):
        expected.append(int(row[0]))
print >> sys.stderr, "done"

assert(len(predicted) == len(expected))

print precision_recall_fscore_support(expected, predicted, average=args.average)
