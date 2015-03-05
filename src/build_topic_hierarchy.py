from gensim.models.ldamodel import LdaModel
import pandas as pd
from pandas.io.pytables import read_hdf
import sys
from sklearn.cluster import AgglomerativeClustering, Ward

import argparse
import os
import pandas as pd
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--modelDir', help='Directory for reading the LDA model', required=True)
parser.add_argument('--modelBaseName', help='Base name for the model', required=True)
parser.add_argument('--nrClusters', help='Number of clusters in which to organize the topic models', required=True)
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
clusterer = AgglomerativeClustering(n_clusters=nrClusters, affinity='euclidean', linkage="ward")
print >> sys.stderr, "Hierarchically clustering topics ...",
hierarchy = clusterer.fit_predict(topicsWordsMatrix)
print >> sys.stderr, "done"

print "hierarchy (%d leaves, %d clusters):" % (topicsWordsMatrix.shape[0], nrClusters), hierarchy 
