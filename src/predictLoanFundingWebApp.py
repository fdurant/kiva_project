#!/usr/bin/python

from flask import Flask, jsonify, make_response
from flask_restful import reqparse, abort, Api, Resource
from sklearn.linear_model import LogisticRegression
import numpy as np
import pandas as pd
from random import random
import json

# IMPORT LOADING AND CREATION OF DEPLOYED MODELS IN SEPARATE PYTHON MODULES
# IDEM FOR ON THE FLY PREPROCESSING OF ALL PREVIOUSLY UNSEEN KIVA LOANS

def getLoanFundingScore(loanId=-1):
    return random()

# Initialize the app
app = Flask(__name__)
api = Api(app)

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
        exampleUri = "http://104.236.210.43/kivapredictor/api/v1.0/loanprediction?loanid=185"
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
        self.data = {"loanFundingScore": getLoanFundingScore(args['loanid'])}
        
    def get(self):
        self.representations = {
            'text/json': output_json
        }
        return self.data
        
api.add_resource(Usage, '/')
api.add_resource(LoanFundingPrediction, '/kivapredictor/api/v1.0/loanprediction')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
