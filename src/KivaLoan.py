import urllib2
import json
from clean_kiva_descriptions import removeHtmlTags, identifyLanguagePerParagraph, date_hook
from kiva_utilities import getMajorityGender, getFundingRatioLabel
from datetime import datetime, date
import re
from math import log10
import langid

class KivaLoan(object):
    ''' Class representing a single loan at kiva.org '''

    def __init__(self, id=None, dict=None):
        assert(id or dict), "At least one named argument must differ from None"
        if id:
            self.id = int(id)
        if dict:
            self.dict = dict
            if id:
                assert(self.id == self.dict['id'])
            else:
                self.id = self.dict['id']
        else:
            self.__initializeFromKivaApi__(self.id)
        self.__addProcessedDescription__()

    def __initializeFromKivaApi__(self,id):
        url = "http://api.kivaws.org/v1/loans/%d.json" % id
        response = urllib2.urlopen(url)
        self.dict = json.load(response, encoding='utf-8', object_hook=date_hook)['loans'][0]

    def __detectParagraphsAndLanguages__(self):
        paragraphsByDetectedLanguage = {}
        for lang in self.dict['description']['texts'].keys():
            desc = unicode(self.dict['description']['texts'][lang])

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

    def __addProcessedDescription__(self):
        paragraphsByDetectedLanguage = self.__detectParagraphsAndLanguages__()
        if paragraphsByDetectedLanguage:
            self.dict['processed_description'] = {}
            self.dict['processed_description']['texts'] = {}
            for (langcode, text) in paragraphsByDetectedLanguage.items():
                self.dict['processed_description']['texts'][langcode] = "\n\n".join(text)

    def getId(self):
        return self.id

    def getLoanAmount(self):
        return self.dict['loan_amount']

    def getPartnerId(self):
        return self.dict['partner_id']

    def getFundedAmount(self):
        return self.dict['funded_amount']

    def getFundingRatioLabel(self):
        return getFundingRatioLabel(self.getFundedAmount(), self.getLoanAmount(), posCutoff=1.0, negCutoff=1.0)

    def getLog10LoanAmount(self):
        return log10(self.getLoanAmount())

    def getBorrowers(self):
        return self.dict['borrowers']

    def getMajorityGender(self,transformCategorical=False):
        result = getMajorityGender(self.getBorrowers())
        if transformCategorical:
            if result == u'M':
                return 1
            else:
                return 0
        else:
            return result 

    def getImage(self):
        return self.dict['image']

    def getHasImage(self,transformCategorical=False):
        result = self.getImage() is not None
        if transformCategorical:
            return 1 if result else 0
        else:
            return result

    def getPostedDayOfMonth(self):
        try:
            return self.dict['posted_date'].day
        except:
            return date.today().day

    def getPostedMonth(self, testedMonth):
        assert(testedMonth in range(1,13))
        try:
            actualMonth = self.dict['posted_date'].month
            return actualMonth == testedMonth
        except:
            return False

    def getPostedMonthJan(self):
        return self.getPostedMonth(1)

    def getPostedMonthFeb(self):
        return self.getPostedMonth(2)

    def getPostedMonthMar(self):
        return self.getPostedMonth(3)

    def getPostedMonthApr(self):
        return self.getPostedMonth(4)

    def getPostedMonthMay(self):
        return self.getPostedMonth(5)

    def getPostedMonthJun(self):
        return self.getPostedMonth(6)

    def getPostedMonthJul(self):
        return self.getPostedMonth(7)

    def getPostedMonthAug(self):
        return self.getPostedMonth(8)

    def getPostedMonthSep(self):
        return self.getPostedMonth(9)

    def getPostedMonthOct(self):
        return self.getPostedMonth(10)

    def getPostedMonthNov(self):
        return self.getPostedMonth(11)

    def getPostedMonthDec(self):
        return self.getPostedMonth(12)

    def getGeoLatitude(self):
        return float(re.split("\s+",self.dict['location']['geo']['pairs'])[0])

    def getGeoLongitude(self):
        return float(re.split("\s+",self.dict['location']['geo']['pairs'])[1])

    def getRepaymentTerm(self):
        return self.dict['terms']['repayment_term']

    def getNumberOfBorrowers(self):
        return len(self.getBorrowers())

    def getLog10NumberOfBorrowers(self):
        return log10(self.getNumberOfBorrowers())

    def getBonusCreditEligibility(self,transformCategorical=False):
        result = self.dict['bonus_credit_eligibility']
        if transformCategorical:
            return 1 if result else 0
        else:
            return result

    def getHasTranslator(self,transformCategorical=False):
        result = self.dict.has_key('translator')
        if transformCategorical:
            return 1 if result else 0
        else:
            return result

    def getEnglishDescription(self):
        try:
            return self.dict['processed_description']['texts']['en']
        except:
            # Description containing one bogus word
            return "fkdsfkdsjfkl"

    def getEnglishDescriptionLength(self):
        try:
            # Poor man's tokenization good enough here
            return len(re.split("\s+",self.dict['processed_description']['texts']['en']))
        except:
            return 0

    def getLog10EnglishDescriptionLength(self):
        len = self.getEnglishDescriptionLength()
        if len == 0:
            # Approximation
            return log10(1)
        else:
            return log10(len)

    def getMultipleFeatures(self, 
                            fieldList=['Log10LoanAmount',
                                       'MajorityGender',
                                       'PostedMonthJan',
                                       'PostedMonthFeb',
                                       'PostedMonthMar',
                                       'PostedMonthApr',
                                       'PostedMonthMay',
                                       'PostedMonthJun',
                                       'PostedMonthJul',
                                       'PostedMonthAug',
                                       'PostedMonthSep',
                                       'PostedMonthOct',
                                       'PostedMonthNov',
                                       'PostedMonthDec',
                                       'GeoLatitude',
                                       'GeoLongitude',
                                       'RepaymentTerm',
                                       'Log10NumberOfBorrowers',
                                       'BonusCreditEligibility'],
                            transformCategorical=False):
        result = []
        for f in sorted(fieldList):
            try:
                function = "self.get%s(transformCategorical=transformCategorical)" % f
                result.append((f,eval(function)))
            except:
                function = "self.get%s()" % f
                result.append((f,eval(function)))                
        return result

if __name__ == "__main__":

    dict1 = {"id":844974,"name":"Yaqout","description":{"languages":["en"],"texts":{"en":"Yaqout lives in Al Hashmiya. Her father is employed in Saudi Arabia but his income does not cover all of the family's needs.\r\n\r\nShe has decided to study political management and seek work in this field. She is tired of the political and security situation in the world these days and wants to help find solutions for it. \r\n\r\nHer family's financial difficulty means they cannot cover all her university fees. Yaqout has applied for a loan to help pay her semester fees and achieve her dreams."}},"status":"in_repayment","funded_amount":725,"paid_amount":67.06,"image":{"id":1821760,"template_id":1},"activity":"Higher education costs","sector":"Education","themes":["Higher Education"],"use":"To pay semester fees","location":{"country_code":"JO","country":"Jordan","town":"Hashmiya","geo":{"level":"country","pairs":"31 36","type":"point"}},"partner_id":185,"posted_date":datetime.strptime("2015-02-26T17:40:08Z","%Y-%m-%dT%H:%M:%SZ"),"planned_expiration_date":"2015-03-28T17:40:07Z","loan_amount":725,"lender_count":24,"bonus_credit_eligibility":True,"tags":[{"name":"user_favorite"}],"borrowers":[{"first_name":"Yaqout","last_name":"","gender":"F","pictured":True}],"terms":{"disbursal_date":"2015-02-18T08:00:00Z","disbursal_currency":"JOD","disbursal_amount":500,"repayment_interval":"Monthly","repayment_term":15,"loan_amount":725,"local_payments":[{"due_date":"2015-04-04T07:00:00Z","amount":46.25},{"due_date":"2015-05-05T07:00:00Z","amount":41.25},{"due_date":"2015-06-04T07:00:00Z","amount":41.25},{"due_date":"2015-07-05T07:00:00Z","amount":41.25},{"due_date":"2015-08-04T07:00:00Z","amount":41.25},{"due_date":"2015-09-04T07:00:00Z","amount":41.25},{"due_date":"2015-10-05T07:00:00Z","amount":41.25},{"due_date":"2015-11-04T08:00:00Z","amount":41.25},{"due_date":"2015-12-05T08:00:00Z","amount":41.25},{"due_date":"2016-01-04T08:00:00Z","amount":41.25},{"due_date":"2016-02-04T08:00:00Z","amount":41.25},{"due_date":"2016-03-06T08:00:00Z","amount":41.25}],"scheduled_payments":[{"due_date":"2015-06-01T07:00:00Z","amount":67.07},{"due_date":"2015-07-01T07:00:00Z","amount":59.82},{"due_date":"2015-08-01T07:00:00Z","amount":59.82},{"due_date":"2015-09-01T07:00:00Z","amount":59.81},{"due_date":"2015-10-01T07:00:00Z","amount":59.81},{"due_date":"2015-11-01T07:00:00Z","amount":59.81},{"due_date":"2015-12-01T08:00:00Z","amount":59.81},{"due_date":"2016-01-01T08:00:00Z","amount":59.81},{"due_date":"2016-02-01T08:00:00Z","amount":59.81},{"due_date":"2016-03-01T08:00:00Z","amount":59.81},{"due_date":"2016-04-01T07:00:00Z","amount":59.81},{"due_date":"2016-05-01T07:00:00Z","amount":59.81}],"loss_liability":{"nonpayment":"lender","currency_exchange":"shared","currency_exchange_coverage_rate":0.1}},"payments":[{"amount":67.06,"local_amount":46.25,"processed_date":"2015-02-28T08:00:00Z","settlement_date":"2015-03-19T10:56:36Z","rounded_local_amount":47.56,"currency_exchange_loss_amount":0,"payment_id":624884967}],"funded_date":"2015-02-26T21:01:34Z","journal_totals":{"entries":0,"bulkEntries":0},"translator":{"byline":"Michael Ernest","image":627833}}

    id1 = 844974
    loan1a = KivaLoan(id=id1, dict=dict1)
    assert(loan1a.getId() == id1)
    assert(loan1a.getLoanAmount() == 725)

    loan1b = KivaLoan(dict=dict1)
    assert(loan1b.getId() == id1)
    assert(loan1b.getLoanAmount() == 725)

#    loan1c = KivaLoan(id=str(id1))
    loan1c = KivaLoan(dict=dict1)
    assert(loan1c.getId() == id1)
    assert(loan1c.getLoanAmount() == 725)
    assert(loan1c.getPartnerId() == 185)
    assert(loan1c.getFundedAmount() == 725)
    assert(loan1c.getFundingRatioLabel() == 1)
    assert(round(pow(10,loan1c.getLog10LoanAmount())) == 725.0)
    assert(loan1c.getMajorityGender() == 'F')
    assert(loan1c.getHasImage())
    assert(loan1c.getPostedDayOfMonth() == 26),"found %d" % loan1c.getPostedDayOfMonth()
    assert(not loan1c.getPostedMonthJan())
    assert(not loan1c.getPostedMonth(1))
    assert(loan1c.getPostedMonthFeb())
    assert(loan1c.getPostedMonth(2))
    assert(not loan1c.getPostedMonthMar())
    assert(not loan1c.getPostedMonth(3))
    assert(loan1c.getGeoLatitude() == 31.0)
    assert(loan1c.getGeoLongitude() == 36.0)
    assert(loan1c.getRepaymentTerm() == 15)
    assert(loan1c.getNumberOfBorrowers() == 1)
    assert(round(pow(10,loan1c.getLog10NumberOfBorrowers())) == 1.0)
    assert(loan1c.getBonusCreditEligibility() == True)
    assert(loan1c.getHasTranslator() == True)
    assert(len(loan1c.getEnglishDescription()) == 487)
    assert(loan1c.getEnglishDescriptionLength() == 86)
    assert(round(pow(10,loan1c.getLog10EnglishDescriptionLength())) == 86.0)

    print loan1c.getMultipleFeatures()
