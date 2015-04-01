#!/usr/bin/python

from flask import Flask, jsonify, make_response
from flask_restful import reqparse, abort, Api, Resource
from sklearn.linear_model import LogisticRegression
import numpy as np
import pandas as pd
from random import random
import json
import pickle
from KivaLoans import KivaLoans
from KivaLoan import KivaLoan
from KivaLoanFundingPredictor import KivaLoanFundingPredictor
from os.path import expanduser
from SldaTextFeatureGenerator import SldaTextFeatureGenerator

def getLoanFundingScore(kivaLoans):
    loans = kivaLoans.getLoanIds()

    columns, features = kivaLoans.getAllFeatures(slda, settingsFile, transformCategorical=True)

    loansDF = pd.DataFrame.from_items(zip(loans, features), columns=columns, orient='index')

    probaList = predictor.predict_proba(X=loansDF)
    predictions = predictor.predict(X=loansDF)

    return (probaList[0].tolist()[1],predictions[0])

# Initialize the app
app = Flask(__name__)
api = Api(app)

global predictor
predictor = KivaLoanFundingPredictor()
predictor.loadFromDisk('data/predicting_funding/logres_out/kivaLoanFundingPredictor.pkl')

global slda
homeDir = expanduser("~")
projectDir = "%s/%s" % (homeDir, 'work/metis_projects/passion_project/kiva_project')
sldaBin = "%s/%s" % (homeDir, 'install/slda-master/slda')
modelFileBin = "%s/%s" % (projectDir, 'data/predicting_funding/slda_out/final.model')
modelFileTxt = "%s/%s" % (projectDir, 'data/predicting_funding/slda_out/final.model.text')
dictionaryFile = "%s/%s" % (projectDir, 'data/predicting_funding/kiva_dict.txt')
vocabFile = "%s/%s" % (projectDir, 'data/predicting_funding/kiva.lda-c.vocab')
slda = SldaTextFeatureGenerator(modelFileBin=modelFileBin,
                                modelFileTxt=modelFileTxt,
                                dictionaryFile=dictionaryFile,
                                vocabFile=vocabFile,
                                sldaBin=sldaBin)
global settingsFile
settingsFile = "%s/%s" % (projectDir, 'data/predicting_funding/slda_settings.txt')

@api.representation('application/json')
def output_json(data, code, headers=None):
    """Makes a Flask response with a JSON encoded body"""
    resp = make_response(json.dumps(data), code)
    resp.headers.extend(headers or {})
    return resp

@api.representation('text/html')
def output_html(data, code, headers=None):
    """Makes a Flask response with an HTML encoded body"""
    html = "<html><body><table>"
    for k,v in data.items():
        html += "<tr><td>%s</td><td>%s</td></tr>\n" % (k,v)
    html += "</table></body></html>"
    resp = make_response(html, code)
    resp.headers.extend(headers or {})
    return resp
    

class Usage(Resource):
    def __init__(self):
        exampleUri = "http://104.236.210.43/kivapredictor/api/v1.0/loanprediction?loanid=844974"
        self.data = {"Usage": '<a href="%s">%s</a>' % (exampleUri, exampleUri)}

    def get(self):
        self.representations = {
            'text/html': output_html
        }
        return self.data
        
class LoanFundingPrediction(Resource):

    def __init__(self):
        
        parser = reqparse.RequestParser()
        parser.add_argument('loanid', 
                            type=int, 
                            help='ID of a single loan as returned by http://build.kiva.org/api#GET*|loans|:ids',
                            location='args',
                            required=True)
        args = parser.parse_args()
        
        kivaLoan = KivaLoan(id=args['loanid'])
        kivaLoans = KivaLoans()
        kivaLoans.push(kivaLoan)

        (proba, prediction) = getLoanFundingScore(kivaLoans)
        gammas = kivaLoans.getTopicFeatures(slda=slda, settingsFile=settingsFile)[0]
        topics = slda.getTopics(nrWordsPerTopic=10, sortedByDescendingEta=False, withEtas=False, withBetas=False)
        
        print "gammas =", gammas
        print "topics =", topics

        topicScores = sorted(zip(topics,gammas), key=lambda x:x[1][1], reverse=True)

        self.data = {"loanFundingScore": proba,
                     "loanId":args['loanid'],
                     "prediction": prediction,
                     "topicScores": topicScores}
        
    def get(self):
        self.representations = {
            'text/json': output_json
        }
        return self.data
        
api.add_resource(Usage, '/')
api.add_resource(LoanFundingPrediction, '/kivapredictor/api/v1.0/loanprediction')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
