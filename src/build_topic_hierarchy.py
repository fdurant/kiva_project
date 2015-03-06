from gensim import corpora, models
from gensim.models.ldamodel import LdaModel
import pandas as pd
from pandas.io.pytables import read_hdf
import sys
from sklearn.cluster import AgglomerativeClustering, Ward
from pprint import pprint
import json

import argparse
import os
import pandas as pd
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--modelDir', help='Directory for reading the LDA model', required=True)
parser.add_argument('--modelBaseName', help='Base name for the model', required=True)
parser.add_argument('--nrClusters', help='Number of clusters in which to organize the topic models', required=True)
parser.add_argument('--nrWords', help='Number of words to show per topic', default=10)
args = parser.parse_args()

topicWordsMatrixFile = "%s/%s_topic_words_matrix.h5" % (args.modelDir, args.modelBaseName)
print >> sys.stderr, "Reading topic/word matrix file %s ..." % topicWordsMatrixFile,
topicsWordsMatrix = read_hdf(topicWordsMatrixFile, 'table')
print >> sys.stderr, "done"

#print topicsWordsMatrix

# Now do a hierarchical clustering of the topics
#from sklearn.neighbors import kneighbors_graph
#connectivity = kneighbors_graph(X, n_neighbors=10)

nrClusters = int(args.nrClusters)
nrWords = int(args.nrWords)
clusterer = AgglomerativeClustering(n_clusters=nrClusters, affinity='euclidean', linkage="ward")
print >> sys.stderr, "Hierarchically clustering topics ...",
hierarchy = clusterer.fit_predict(topicsWordsMatrix)
print >> sys.stderr, "done"

print "hierarchy (%d leaves, %d clusters):" % (topicsWordsMatrix.shape[0], nrClusters), hierarchy 


modelFile = "%s/%s.lda_model" % (args.modelDir, args.modelBaseName)
modelDir = args.modelDir
print >> sys.stderr, "Loading model file %s ..." % modelFile,
ldaModel = LdaModel.load(modelFile)
print >> sys.stderr, "done"
topicsAsWeightedWordVectors = ldaModel.show_topics(num_topics=len(hierarchy),formatted=False)
#print topicsAsWeightedWordVectors

def mergeWeightedWords(listsOfWeightedWordTupleLists):
    '''
    Input is a list of N-length lists of (weight, word) tuples
    Output is an N-length sorted list of (weight, word tuples)
    We'll start with a naive implementation that just assembles the sublists and takes the N with the highest weights
    '''

    print "listsOfWeightedWordTupleLists = ", listsOfWeightedWordTupleLists
    print

    result = []
    n = len(listsOfWeightedWordTupleLists[0])
    words2weightSums = {}
    for l in listsOfWeightedWordTupleLists[1:]:
        assert(n == len(l))
    for l in listsOfWeightedWordTupleLists:
        for weight, word in l:
#            print "weight =", weight
#            print "word =", word
            if words2weightSums.has_key(word):
                words2weightSums[word] += weight
            else:
                words2weightSums[word] = weight

    # Take the top-n
    return [elem for elem in sorted(words2weightSums.items(), key=lambda x:words2weightSums[x[0]])][0:n]

def processHierarchyLevel(hierarchy, clusterId, topicIndex):

    print "Entering processHierarchyLevel with clusterID %d and topicIndex %d" % (clusterId, topicIndex)

    result = {}
    result[unicode('name')] = unicode('topic_%d' % topicIndex)

    # Special case: we're at the bottom of the recursion
    if clusterId <= 0:
        topWeightedWords = topicsAsWeightedWordVectors[topicIndex][0:nrWords]
        print "topWeightedWords = ", topWeightedWords
        result[unicode('words')] = [w[1] for w in topWeightedWords]
        result[unicode('weightedWords')] = [w for w in topWeightedWords]
    else:
        childrenWeightedWords = []
        children = []
        for i, cid in enumerate(hierarchy):
        # Find all the topics that are clustered at this level, and join them
            if cid == clusterId:
                child = processHierarchyLevel(hierarchy=hierarchy,clusterId=clusterId-1,topicIndex=list(hierarchy).index(clusterId-1))
#                print "child is ",
#                pprint(child)
                childrenWeightedWords.append(child[unicode('weightedWords')])
                # We may have to throw this away later, unless it doesn't hurt for D3/Hierarchie
                #del child[unicode('weightedWords')]
                children.append(child)
        mergedWeightedWords = mergeWeightedWords(childrenWeightedWords)
        result[unicode('words')] = [elem[1] for elem in mergedWeightedWords]
        result[unicode('weightedWords')] = mergedWeightedWords
        result[unicode('children')] = children
    return result

def buildD3Hierarchy(hierarchy):
    '''
    topicsAsWeightedWordVectors is a global variable (!!!)
    Hierarchy is a list of numbers from 0 through nrClusters. The position of each number corresponds with the
    position of the topic in topicsAsWeightedWordVectors
    '''
    
    assert(len(topicsAsWeightedWordVectors) == len(hierarchy)), "Found a different number of topics in the topic list (%d) as in the hierarchy (%d)!" % (len(topicsAsWeightedWordVectors), len(hierarchy))
    
    topClusterId = max(hierarchy)

    # Start at the top of the hierarchy, building it recursively
    result = {}
    result[unicode('topic_data')] = processHierarchyLevel(hierarchy=hierarchy,
                                                          clusterId=topClusterId,
                                                          topicIndex=list(hierarchy).index(topClusterId))
    return result

print >> sys.stderr, "Building nested hierarchy in memory ..."
d3Hierarchy = buildD3Hierarchy(hierarchy)
print "done"

print >> sys.stderr, "Dumping object hierarchy into JSON file %s ..." % modelFile,
jsonFile = "%s/%s_topic_hierarchy.json" % (args.modelDir, args.modelBaseName)
with open(jsonFile, 'w') as outfile:
    json.dump(d3Hierarchy, outfile)
print "done"
