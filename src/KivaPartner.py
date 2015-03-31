import urllib2
from datetime import datetime
import json
from clean_kiva_descriptions import date_hook


class KivaPartner(object):
    ''' Class representing a single Kiva Partner '''

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

    @classmethod
    def __initializeFromKivaApi__(self,id):
        url = "http://api.kivaws.org/v1/partners/%d.json" % id
        response = urllib2.urlopen(url)
        self.dict = json.load(response, encoding='utf-8', object_hook=date_hook)['partners'][0]

    def getId(self):
        return self.id

    def getStatus(self):
        return self.dict['status']

    def getRating(self):
        return float(self.dict['rating'])
        
    def getDelinquencyRate(self):
        return float(self.dict['delinquency_rate'])
        
    def getLoansPosted(self):
        return self.dict['loans_posted']
        
    def getTotalAmountRaised(self):
        return self.dict['total_amount_raised']

    def getMultipleFeatures(self,
                            fieldList=['Rating',
                                       'DelinquencyRate',
                                       'LoansPosted',
                                       'TotalAmountRaised']):
        result = []
        for f in sorted(fieldList):
            function = "self.get%s()" % f
            try:
                res = (f,eval(function))
            except:
                res = (f,None)
            result.append(res)
        return result
        
if __name__ == "__main__":

    dict1 = {"id":185,"name":"National Microfinance Bank","status":"active","rating":"3.5","image":{"id":790950,"template_id":1},"start_date":datetime.strptime("2011-03-30T22:00:05Z","%Y-%m-%dT%H:%M:%SZ"),"countries":[{"iso_code":"JO","region":"Middle East","name":"Jordan","location":{"geo":{"level":"country","pairs":"31 36","type":"point"}}}],"delinquency_rate":0.52972978609596,"default_rate":0.70201247428837,"total_amount_raised":4604300,"loans_posted":4364,"portfolio_yield":38,"profitability":11,"social_performance_strengths":[{"id":1,"name":"Anti-Poverty Focus","description":"The work of most microfinance institutions helps to combat poverty, but these Field Partners do even more."},{"id":7,"name":"Innovation","description":"These Field Partners embrace technology and innovation to better address the needs of the people they serve."}],"delinquency_rate_note":"","default_rate_note":"","portfolio_yield_note":"","charges_fees_and_interest":True,"average_loan_size_percent_per_capita_income":13.3,"loans_at_risk_rate":2.8073454785428,"currency_exchange_loss_rate":0,"url":"http:\/\/www.nmb.com.jo"}

    id1 = 185
    partner1a = KivaPartner(id=id1, dict=dict1)
    assert(partner1a.getId() == id1)

    partner1b = KivaPartner(dict=dict1)
    assert(partner1b.getId() == id1)

#    partner1c = KivaPartner(id=str(id1))
    partner1c = KivaPartner(dict=dict1)
    assert(partner1c.getId() == id1)
    assert(partner1c.getRating() == 3.5)
    assert(partner1c.getStatus() == 'active')
    assert(partner1c.getDelinquencyRate() == 0.52972978609596)
    assert(partner1c.getLoansPosted() == 4364)
    assert(partner1c.getTotalAmountRaised() == 4604300)
