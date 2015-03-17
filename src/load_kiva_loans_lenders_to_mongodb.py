import json
import glob
import codecs
import sys
from pymongo import MongoClient

loanLenderFiles = glob.glob("./data/static/loans_lenders/*.json")
nrLoanLenderFiles = len(loanLenderFiles)

client = MongoClient()
loanLenderCollection = client.kiva.loanslenders

for i, file in enumerate(loanLenderFiles):
    print >> sys.stderr, "Processing loans/lenders file %d/%d ..." % (i+1, nrLoanLenderFiles),
    with codecs.open(file, "rb", encoding='utf-8') as f:
        j = json.loads(f.read())

        for entry in j['loans_lenders']:
            try:
                loanLenderCollection.save(entry)
            except:
                print >> sys.stderr, "Could not save loan/lender with id %s" % entry['id']
    print >> sys.stderr, "done"

loanLenderCollection.create_index("id")
