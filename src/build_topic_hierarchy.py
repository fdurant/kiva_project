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
import random
import pickle
import argparse
import os
import pandas as pd
import numpy as np

from recursive_kmeans import myclustering

def parseArguments():

    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--modelDir', help='Directory for reading the LDA model', required=True)
    parser.add_argument('--modelBaseName', help='Base name for the model', required=True)
    parser.add_argument('--nrClusters', help='Number of clusters in which to organize the topic models', required=True)
    parser.add_argument('--nrWords', help='Number of words to show per topic', default=10)
    args = parser.parse_args()

def readTopicWordsMatrix():

    global topicsWordsMatrix
    topicWordsMatrixFile = "%s/%s_topic_words_matrix.h5" % (args.modelDir, args.modelBaseName)
    print >> sys.stderr, "Reading topic/word matrix file %s ..." % topicWordsMatrixFile,
    topicsWordsMatrix = read_hdf(topicWordsMatrixFile, 'table')
    print >> sys.stderr, "done"

#    print topicsWordsMatrix

def clusterTopics():

    global hierarchy
    global nrClusters
    global nrWords

    nrClusters = int(args.nrClusters)
    nrWords = int(args.nrWords)
    print >> sys.stderr, "Hierarchically clustering topics ...",

    hierarchy = myclustering(topicsWordsMatrix, branching_factor=nrClusters)
    print "recursive hierarchy:"
    pprint(hierarchy)

    #ALTERNATIVE CLUSTERING
    #clusterer = AgglomerativeClustering(n_clusters=nrClusters, affinity='euclidean', linkage="ward")
    #hierarchy = clusterer.fit_predict(topicsWordsMatrix)
    #hierarchy = [0,1,2,3,4,0,1,2,3,4,0,1,2,3,4,0,1,2,3,4,0,1,2,3,4,0]

    #OTHER ALTERNATIVE CLUSTERING LIBRARY
    #For examples, see
    #http://nbviewer.ipython.org/github/rasbt/pattern_classification/blob/master/clustering/hierarchical/clust_complete_linkage.ipynb
    #http://nbviewer.ipython.org/github/OxanaSachenkova/hclust-python/blob/master/hclust.ipynb
    #For documentation, see
    #http://docs.scipy.org/doc/scipy/reference/cluster.hierarchy.html

    #data_dist = pdist(topicsWordsMatrix) # computing the distance
    #data_link = linkage(data_dist) # computing the linkage
    #hierarchy = fclusterdata(data_link, 20, criterion='maxclust', depth=2)
    #print "data_link:"
    #print data_link 

    #print "hierarchy:", hierarchy 
    #exit()
    print >> sys.stderr, "done"

def loadLDAModelFile():

    global topicsAsWeightedWordVectors
    modelFile = "%s/%s.lda_model" % (args.modelDir, args.modelBaseName)
    modelDir = args.modelDir
    print >> sys.stderr, "Loading model file %s ..." % modelFile,
    ldaModel = LdaModel.load(modelFile)
    print >> sys.stderr, "done"
    topicsAsWeightedWordVectors = ldaModel.show_topics(num_topics=topicsWordsMatrix.shape[0],num_words=nrWords,formatted=False)
#    print "topicsAsWeightedWordVectors = "
#    pprint(topicsAsWeightedWordVectors)

def loadInferredDistributions():
    
    global topicDistributionsAllDocs
    topicDistributionsFile = "%s/%s_topic_distributions.p" % (args.modelDir, args.modelBaseName)
    with open(topicDistributionsFile, 'rb') as pickleFile:
        topicDistributionsAllDocs = pickle.load(pickleFile)

def mergeWeightedWords(listsOfWeightedWordTupleLists,sizes):
    '''
    listsOfWeightedWordTupleLists is a list of N-length lists of (weight, word) tuples
    sizes is a list of sizes
    Output is a summary N-length sorted list of (weight, word tuples) weighted by size
    We'll start with a naive implementation that just assembles the sublists and takes the N with the highest weights
    '''

#    print "listsOfWeightedWordTupleLists = " 
#    pprint(listsOfWeightedWordTupleLists)
#    print

    assert(len(listsOfWeightedWordTupleLists) == len(sizes))

    totalSizes = sum(sizes)

    result = []
    n = len(listsOfWeightedWordTupleLists[0])
    words2weightSums = {}
    for l in listsOfWeightedWordTupleLists[1:]:
        assert(n == len(l))
    for i,l in enumerate(listsOfWeightedWordTupleLists):
        for tuple in l:
#            print "tuple = ", tuple
            weight = float(tuple[0]) # Convert from numpy.float64 to native float
            word = tuple[1]
            size = sizes[i]
            assert(type(weight)==type(0.0)), "%f" % weight
            assert(type(word) == type(u'abc')), "%s" % word
            if words2weightSums.has_key(word):
                words2weightSums[word] += (weight*size)/totalSizes
            else:
                words2weightSums[word] = (weight*size)/totalSizes

    # Take the top-n
    result = [(elem[1],elem[0]) for elem in sorted(words2weightSums.items(), key=lambda x:words2weightSums[x[0]], reverse=True)][0:n]
#    print "merged result = "
#    pprint(result)
    return result

def processHierarchyLevel(topics, hierarchy,topicDistributions):

#    print "Entering processHierarchyLevel"
#    print "hierarchy = ", hierarchy

    assert(type(hierarchy) == list)

    result = []

    for elem in hierarchy:

#        print "elem = ", elem
#        print "type(elem) = ", type(elem)
        if type(elem) == type([]):

            # Recursive call returns a list
            children = processHierarchyLevel(topics=topics,
                                             hierarchy=elem,
                                             topicDistributions=topicDistributions)
            
#            print "children = ",
#            pprint(children)
            assert(type(children) == type([])), "Children is not of list type"

            topicIdsChildren = []
            topicDistributionSizes = []
            weightedWords = []

            for child in children:
                familyMember = {}
                assert(type(child) == type({})), "Child is not a dict"
                weightedWords.append(child[unicode('weightedWords')])
                topicDistributionSizes.append(child[unicode('b_size')])
                topicIdsChildren.append(child[unicode('b_name')].replace('topic_',''))

            mergedWeightedWords = mergeWeightedWords(weightedWords,topicDistributionSizes)
            familyMember[unicode('a_words')] = [elem[1] for elem in mergedWeightedWords]
            familyMember[unicode('b_name')] = unicode('topic_%s' % "_".join(topicIdsChildren))
            familyMember[unicode('weightedWords')] = mergedWeightedWords
            familyMember[unicode('b_size')] = int(sum(topicDistributionSizes))
            familyMember[unicode('children')] = children

            result.append(familyMember)

        else:
            # We've reached a leaf, i.e. a topic
            sibling = {} 
    
            topicId = elem
            topWeightedWords = topics[topicId][0:nrWords]
            sibling[unicode('a_words')] = [w[1] for w in topWeightedWords]
            sibling[unicode('b_name')] = unicode('topic_%d' % topicId)
            sibling[unicode('b_size')] = int(topicDistributions[0,topicId])
            sibling[unicode('weightedWords')] = [w for w in topWeightedWords]
            result.append(sibling)

#    print "result = "
#    pprint(result)
    return result

def buildD3Hierarchy(topics, hierarchy,topicDistributions):
    '''
    topics is a list of lists containing (weight, word) tuples
    Hierarchy is a nested list, where the leaves correspond to topicIds
    topicDistributions a numpy ndarray that contains the distribution counts of all documents over topics

    This function returns a nested data structure:
    a list of dict(s) containing lists of dict(s) of lists of dict(s)...
    '''
    
    global nrClusters

    # Start at the top of the hierarchy, building it recursively
    result = {}
    result[unicode('topic_data')] = processHierarchyLevel(topics=topics,
                                                          hierarchy=hierarchy,
                                                          topicDistributions=topicDistributions)
    return result

def removeWeightedWords(tree):
    '''
    Traverse the object and remove this weightedWords information,
    which is not needed by the D3/Hierarchie software
    
    '''
    assert(type(tree) == dict), "tree is not a dict"
    topicName = ""
    if tree.has_key(u'b_name'):
        topicName = tree[u'b_name']
    if tree.has_key(u'children'):
        for c in tree[u'children']:
            removeWeightedWords(c)
    if tree.has_key(u'weightedWords'):
#        print "About to delete in topic %s" % topicName, tree[u'weightedWords'],
        del tree[u'weightedWords']
#        print "done"

def BuildNestedHierarchy():

    global d3Hierarchy
    print >> sys.stderr, "Building nested hierarchy in memory ... ",
    d3Hierarchy = buildD3Hierarchy(topicsAsWeightedWordVectors,hierarchy,topicDistributionsAllDocs)
    for subTree in d3Hierarchy['topic_data']:
        removeWeightedWords(subTree)
    print "done"
    pprint(d3Hierarchy)

def DumpTopicHierarchyIntoJSONFile():

    jsonFile = "%s/%sdata.json" % (args.modelDir, args.modelBaseName)
    print >> sys.stderr, "Dumping object hierarchy into JSON file %s ... " % jsonFile,
    with open(jsonFile, 'w') as outfile:
        tmp = json.dumps(d3Hierarchy, sort_keys=True)
        # Hack to make sure that 'words' and 'name' are found first by the relevant D3 library
        tmp = tmp.replace('a_words','words')
        tmp = tmp.replace('b_name','name')
        tmp = tmp.replace('b_value','value')
        tmp = tmp.replace('b_depth','depth')
        tmp = tmp.replace('b_size','size')
        outfile.write(tmp)
    print "done"

if __name__ == "__main__":
    parseArguments()

    readTopicWordsMatrix()

    clusterTopics()

    loadInferredDistributions()

    loadLDAModelFile()

    BuildNestedHierarchy()

    DumpTopicHierarchyIntoJSONFile()
