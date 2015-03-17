import json
import glob
import codecs
import sys
from clean_kiva_descriptions import date_hook
from pymongo import MongoClient
from datetime import datetime

lenderFiles = glob.glob("./data/static/lenders/*.json")
nrLenderFiles = len(lenderFiles)

client = MongoClient()
lenderCollection = client.kiva.lenders

for i, file in enumerate(lenderFiles):
    print >> sys.stderr, "Processing lenders file %d/%d ..." % (i+1, nrLenderFiles),
    with codecs.open(file, "rb", encoding='utf-8') as f:
        j = json.loads(f.read(),object_hook=date_hook)

        for lender in j['lenders']:
            try:
                lenderCollection.save(lender)
            except:
                print >> sys.stderr, "Could not save lender with lender_id %s" % lender['lender_id']
    print >> sys.stderr, "done"

lenderCollection.create_index("lender_id")
lenderCollection.create_index("name")
lenderCollection.create_index("country_code")
lenderCollection.create_index("uid")
lenderCollection.create_index("member_since")
lenderCollection.create_index("loan_count")
lenderCollection.create_index("invitee_count")
lenderCollection.create_index("inviter_id")
