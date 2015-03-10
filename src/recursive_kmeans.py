from sklearn.cluster import KMeans, MiniBatchKMeans
import pandas as pd
from pprint import pprint

def relabel(tree):

    result = []
    return result

def myclustering(topics2Words,branching_factor=6):
    '''
    The function returns a list of topic cluster ids from 0 through (branching_factor**depth)
    where the length of this list is equal to the number of lowest-level topics (i.e.
    the number of rows in the topics2Words matrix)

    '''
    hierarchy = [-1 for i in range(topics2Words.shape[0])]
    tree = recursive_kmeans(topics2Words,branching_factor, hierarchy)
    print "tree =" 
    pprint(tree)

    return hierarchy

# Global variable
clusterIdCountUp=0

def recursive_kmeans(topics2Words,branching_factor,hierarchyAsList):
    '''
    Starting from a topics x words matrix (i.e. from the result of topic mapping),
    we produce a balanced hierarchy of these topics by recursively applying Kmeans
    clustering (with constant K across recursions), until we can't cluster anymore

    The function returns a nested list of lists, where the leaves are the original row numbers of topics2Words

    '''

    global clusterIdCountUp

    # Used to keep track across nodes and subnodes
    result = []

    nrTopics = topics2Words.shape[0]
    
    assert(type(topics2Words) == pd.core.frame.DataFrame)
    assert(type(branching_factor) == int)
    assert(branching_factor >= 2)
    assert(branching_factor <= 10) # So we can use the decimal digit to build a hierarchically aware ID

    # Do KMeans clustering at this level
    model = KMeans(n_clusters=branching_factor, init='k-means++', n_init=10)
    clusters = model.fit_predict(topics2Words)
    
    print "clusters = ", clusters
    print "dataframe indices =", list(topics2Words.index.values)
    clusterCounts = {}
    for cid in clusters:
        if clusterCounts.has_key(cid):
            clusterCounts[cid] += 1
        else:
            clusterCounts[cid] = 1
    print "clusterCounts = ", clusterCounts

    for c in sorted(range(branching_factor), key=lambda x:clusterCounts[x], reverse=True):        
        topicIndicesThisCluster = [i for i,x in enumerate(clusters) if x == c]
#        print "topicIndicesThisCluster = ", topicIndicesThisCluster
        subMatrix = topics2Words.iloc[topicIndicesThisCluster]
#        print "subMatrix.shape = ", subMatrix.shape

        if len(topicIndicesThisCluster) > branching_factor:
            subres = recursive_kmeans(subMatrix,branching_factor,hierarchyAsList)
            result.append(subres)
        else:
            topicIndicesInMatrix=[list(topics2Words.index.values)[i] for i in topicIndicesThisCluster]
            result.append(topicIndicesInMatrix)
            for idx in topicIndicesInMatrix:
                if hierarchyAsList[idx] == -1:
                    print "hierarchyAsList[%d] = %d" % (idx, clusterIdCountUp)
                    hierarchyAsList[idx] = clusterIdCountUp
            clusterIdCountUp += 1

    print
    return result

if __name__ == "__main__":

    tree2 = []
    relabeledTree2 = []
    assert(relabel(tree2) == relabeledTree2), relabeledTree2

    tree1 = [0,[1,2]]
    relabeledTree1 = [1,0,0]
    assert(relabel(tree1) == relabeledTree1), relabeledTree1

