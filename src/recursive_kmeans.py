from sklearn.cluster import KMeans
import pandas as pd
from pprint import pprint

def myclustering(topics2Words,branching_factor=4):
    '''
    The function returns a list of topic cluster ids from 0 through (branching_factor**depth)
    where the length of this list is equal to the number of lowest-level topics (i.e.
    the number of rows in the topics2Words matrix)

    '''
    tree = recursive_kmeans(topics2Words,branching_factor)

    return tree


def recursive_kmeans(topics2Words,branching_factor):
    '''
    Starting from a topics x words matrix (i.e. from the result of topic mapping),
    we produce a hierarchy of these topics by recursively applying Kmeans
    clustering (with constant K across recursions), until we can't cluster anymore

    The function returns a nested list of lists, where the leaves are the original row numbers of topics2Words

    '''

    # Used to keep track across nodes and subnodes
    result = []

    nrTopics = topics2Words.shape[0]
    
    assert(type(topics2Words) == pd.core.frame.DataFrame)
    assert(type(branching_factor) == int)
    assert(branching_factor >= 2)

    # Do KMeans clustering at this level
#    model = KMeans(n_clusters=branching_factor, init='k-means++', n_init=10)
    model = KMeans(n_clusters=branching_factor, init='random', n_init=500)
    clusters = model.fit_predict(topics2Words)
    
#    print "clusters = ", clusters
#    print "dataframe indices =", list(topics2Words.index.values)
    clusterCounts = {}
    for cid in clusters:
        if clusterCounts.has_key(cid):
            clusterCounts[cid] += 1
        else:
            clusterCounts[cid] = 1
#    print "clusterCounts = ", clusterCounts

    for c in sorted(range(branching_factor), key=lambda x:clusterCounts[x], reverse=True):        
        topicIndicesThisCluster = [i for i,x in enumerate(clusters) if x == c]
#        print "topicIndicesThisCluster = ", topicIndicesThisCluster
        subMatrix = topics2Words.iloc[topicIndicesThisCluster]
#        print "subMatrix.shape = ", subMatrix.shape

        if len(topicIndicesThisCluster) > branching_factor:
            subres = recursive_kmeans(subMatrix,branching_factor)
            result.append(subres)
        else:
            topicIndicesInMatrix=[list(topics2Words.index.values)[i] for i in topicIndicesThisCluster]
            if len(topicIndicesInMatrix) == 1:
                result.append(topicIndicesInMatrix[0])
            else:
                result.append(topicIndicesInMatrix)

#    print
    return result

if __name__ == "__main__":

    pass
