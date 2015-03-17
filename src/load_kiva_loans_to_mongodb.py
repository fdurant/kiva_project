import json
import glob
from pprint import pprint
import langid
import codecs
from clean_kiva_descriptions import removeHtmlTags, identifyLanguagePerParagraph, date_hook
import sys
from pymongo import MongoClient, TEXT
from datetime import datetime

loanFiles = glob.glob("./data/static/loans/*.json")
nrLoanFiles = len(loanFiles)

def detectParagraphsAndLanguages(loan):
    paragraphsByDetectedLanguage = {}
    for lang in loan['description']['texts'].keys():
        desc = loan['description']['texts'][lang]

        detectedParagraphsAndLanguages = identifyLanguagePerParagraph(desc)

        for e in detectedParagraphsAndLanguages:
            detectedLang = e[0]
            detectedParagraph = e[1]
            if detectedParagraph != "":
                if paragraphsByDetectedLanguage.has_key(detectedLang):
                    paragraphsByDetectedLanguage[detectedLang].append(detectedParagraph)
                else:
                    paragraphsByDetectedLanguage[detectedLang] = [detectedParagraph]
                            
    return paragraphsByDetectedLanguage

client = MongoClient()
loanCollection = client.kiva.loans

for i, file in enumerate(loanFiles[:]):
    print >> sys.stderr, "Processing loans file %d/%d ..." % (i+1, nrLoanFiles),
    with codecs.open(file, "rb", encoding='utf-8') as f:
        j = json.loads(f.read(),object_hook=date_hook)

        for loan in j['loans']:
#            print loan['id']
            paragraphsByDetectedLanguage = detectParagraphsAndLanguages(loan)                            
            if paragraphsByDetectedLanguage:
                loan['processed_description'] = {}
                loan['processed_description']['texts'] = {}
                for (langcode, text) in paragraphsByDetectedLanguage.items():
#                    print "<<< %s >>>" % langcode
                    loan['processed_description']['texts'][langcode] = "\n\n".join(text)
            try:
#                alreadyExists = len(list(loanCollection.find({'id': loan['id']}))) >= 1
#                if not alreadyExists:
                loanCollection.save(loan)
            except:
                print >> sys.stderr, "Could not save loan with id %s" % loan['id']
#            print loan['processed_description']['texts'][langcode].encode('utf-8','replace')                   
#            print "-" * 80
    print >> sys.stderr, "done"

loanCollection.create_index("id")
loanCollection.create_index("sector")
loanCollection.create_index("posted_date")
loanCollection.create_index("funded_date")
loanCollection.create_index("paid_amount")
loanCollection.create_index("funded_amount")
loanCollection.create_index("loan_amount")
loanCollection.create_index("location.country_code")
loanCollection.create_index("status")
loanCollection.create_index("terms.loan_amount")
loanCollection.create_index("terms.disbursal_amount")
loanCollection.create_index("lender_count")
loanCollection.create_index("activity")

loanCollection.create_index("processed_description")
loanCollection.create_index("processed_description.texts")

# Create the text index
loanCollection.create_index([("processed_description.texts.en",TEXT),
                             ("processed_description.texts.es",TEXT),
                             ("processed_description.texts.fr",TEXT)])
