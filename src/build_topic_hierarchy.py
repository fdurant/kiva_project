from gensim import corpora, models
from gensim.models.ldamodel import LdaModel
import pandas as pd
from pandas.io.pytables import read_hdf
import sys
from sklearn.cluster import AgglomerativeClustering, Ward
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import fclusterdata, linkage, dendrogram
from pprint import pprint
import json

import argparse
import os
import pandas as pd
import numpy as np

from recursive_kmeans import myclustering

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


nrClusters = int(args.nrClusters)
nrWords = int(args.nrWords)
clusterer = AgglomerativeClustering(n_clusters=nrClusters, affinity='euclidean', linkage="ward")
print >> sys.stderr, "Hierarchically clustering topics ...",

hierarchy = myclustering(topicsWordsMatrix, branching_factor=nrClusters)
print "recursive hierarchy:"
pprint(hierarchy)

hierarchy = clusterer.fit_predict(topicsWordsMatrix)
#hierarchy = [0,1,2,3,4,0,1,2,3,4,0,1,2,3,4,0,1,2,3,4,0,1,2,3,4,0]

# ALTERNATIVE CLUSTERING LIBRARY
# For examples, see
# http://nbviewer.ipython.org/github/rasbt/pattern_classification/blob/master/clustering/hierarchical/clust_complete_linkage.ipynb
# http://nbviewer.ipython.org/github/OxanaSachenkova/hclust-python/blob/master/hclust.ipynb
# For documentation, see
# http://docs.scipy.org/doc/scipy/reference/cluster.hierarchy.html

#data_dist = pdist(topicsWordsMatrix) # computing the distance
#data_link = linkage(data_dist) # computing the linkage
#hierarchy = fclusterdata(data_link, 20, criterion='maxclust', depth=2)
#print "data_link:"
#print data_link 

print "hierarchy:", hierarchy 
#exit()
print >> sys.stderr, "done"

topClusterId = max(hierarchy)

# Contains a list of lists
topicIndices = []
for clusterIndex in range(topClusterId+1):
    topicIds = []
    for i in range(len(hierarchy)):
        if hierarchy[i] == clusterIndex:
            topicIds.append(i)
    topicIndices.append(topicIds)

#print "topicIndices ="
#pprint(topicIndices)

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

#    print "listsOfWeightedWordTupleLists = " 
#    pprint(listsOfWeightedWordTupleLists)
#    print

    result = []
    n = len(listsOfWeightedWordTupleLists[0])
    words2weightSums = {}
    for l in listsOfWeightedWordTupleLists[1:]:
        assert(n == len(l))
    for l in listsOfWeightedWordTupleLists:
        for tuple in l:
#            print "tuple = ", tuple
            weight = float(tuple[0]) # Convert from numpy.float64 to native float
            word = tuple[1]
            assert(type(weight)==type(0.0)), "%f" % weight
            assert(type(word) == type(u'abc')), "%s" % word
            if words2weightSums.has_key(word):
                words2weightSums[word] += weight
            else:
                words2weightSums[word] = weight

    # Take the top-n
    result = [(elem[1],elem[0]) for elem in sorted(words2weightSums.items(), key=lambda x:words2weightSums[x[0]], reverse=True)][0:n]
#    print "merged result = "
#    pprint(result)
    return result

def processHierarchyLevel(topics, hierarchy, clusterId, topicIndex, topicIndices):

#    print " " * (nrClusters - clusterId),
#    print "Entering processHierarchyLevel with clusterID %d and topicIndex %d" % (clusterId, topicIndex)
#    print "hierarchy = ", hierarchy

    result = []
    weightedWords = []

    assert(len(topicIndices)>0), "topicIndices must not be empty!"
    for topicId in topicIndices[clusterId]:
#        print "topicId = %d" % topicId
        sibling = {}
        # The 'b_' prefix is a hack to facilitate JSON dumps with ordered keys
        topWeightedWords = topics[topicId][0:nrWords]
#        print "topWeightedWords = "
#        pprint(topWeightedWords)
#        print
        # The 'a_' prefix is a hack to facilitate JSON dumps with ordered keys
        sibling[unicode('a_words')] = [w[1] for w in topWeightedWords]
        sibling[unicode('b_name')] = unicode('topic_%d' % topicId)
        sibling[unicode('weightedWords')] = [w for w in topWeightedWords]
        result.append(sibling)
        weightedWords.append([w for w in topWeightedWords])

    if clusterId > 0:
        children = processHierarchyLevel(topics=topics,
                                         hierarchy=hierarchy,
                                         clusterId=clusterId-1,
                                         topicIndex=list(hierarchy).index(clusterId-1),
                                         topicIndices=topicIndices)
        for child in children:
            weightedWords.append(child[unicode('weightedWords')])
        # We may have to throw this away later, unless it doesn't hurt for D3/Hierarchie
        # del children[unicode('weightedWords')]

        mergedWeightedWords = mergeWeightedWords(weightedWords)
        # Add to the sibling {} that was appended to result above
        result[-1][unicode('a_words')] = [elem[1] for elem in mergedWeightedWords]
        result[-1][unicode('weightedWords')] = mergedWeightedWords
        result[-1][unicode('children')] = children

#    print "RETURNS: "
#    pprint(result)
    return result

def buildD3Hierarchy(topics, hierarchy, topicIndices):
    '''
    topics is a list of lists containing (weight, word) tuples
    Hierarchy is a list of numbers from 0 through nrClusters. The position of each number corresponds with the
    position of the topic in topicsAsWeightedWordVectors
    topicIndices is a lists of lists of indices into topics
    '''
    
    assert(len(topics) == len(hierarchy)), "Found a different number of topics in the topic list (%d) as in the hierarchy (%d)!" % (len(topics), len(hierarchy))
    assert(len(topicIndices) == nrClusters), "The number of elements of topicIndices (%d) must be equal to nrClusters (%d)" % (len(topicIndices), nrClusters)

    topClusterId = max(hierarchy)

    # Start at the top of the hierarchy, building it recursively
    result = {}
    result[unicode('topic_data')] = processHierarchyLevel(topics=topics,
                                                          hierarchy=hierarchy,
                                                          clusterId=topClusterId,
                                                          topicIndex=list(hierarchy).index(topClusterId),
                                                          topicIndices=topicIndices)
    return result

def removeWeightedWords(tree):
    '''
    Traverse the object and remove this weightedWords information,
    which is not needed by the D3/Hierarchie software
    
    '''
    assert(type(tree) == dict), "tree is not a dict"
    if tree.has_key(u'name'):
        topicName = tree['name']
    if tree.has_key(u'children'):
        for c in tree[u'children']:
            removeWeightedWords(c)
    if tree.has_key(u'weightedWords'):
#        print "About to delete in topic %s" % topicName, tree[u'weightedWords'],
        del tree[u'weightedWords']
#        print "done"

print >> sys.stderr, "Building nested hierarchy in memory ... ",
d3Hierarchy = buildD3Hierarchy(topicsAsWeightedWordVectors,hierarchy,topicIndices)
removeWeightedWords(d3Hierarchy['topic_data'][0])
print "done"


jsonFile = "%s/%sdata.json" % (args.modelDir, args.modelBaseName)
print >> sys.stderr, "Dumping object hierarchy into JSON file %s ... " % jsonFile,
with open(jsonFile, 'w') as outfile:
    tmp = json.dumps(d3Hierarchy, sort_keys=True)
    # Hack
    tmp = tmp.replace('a_words','words')
    tmp = tmp.replace('b_name','name')
    outfile.write(tmp)
print "done"
