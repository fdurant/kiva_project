import urllib2
from datetime import datetime
import json
from clean_kiva_descriptions import date_hook

from KivaPartner import KivaPartner

class KivaPartners(object):
    ''' This class represents the collection of all Kiva Partners.
    It exists because we need to calculate mean values for some fields,
    to be used as imputed values for individual Kiva Partners that lack the value at hand.'''

    def __init__(self):
        url = "http://api.kivaws.org/v1/partners.json"
        response = urllib2.urlopen(url)
        dict = json.load(response, encoding='utf-8', object_hook=date_hook)['partners']

        self.allRatings = []
        self.allDelinquencyRates = []

        self.dict = {}
        for p in dict:
            id = p['id']
            
            partner = KivaPartner(dict=p)
            if partner.getStatus() in ['active','paused']:
                try:
                    rating = float(partner.getRating())
                    self.allRatings.append(rating)
                except:
                    # We only take existing ratings into account to calculate the mean
                    pass
                try:
                    delinquencyRate = float(partner.getDelinquencyRate())
                    self.allDelinquencyRates.append(delinquencyRate)
                except:
                    # We only take existing ratings into account to calculate the mean
                    pass
            self.dict[id] = partner

    def getAverageRating(self):
        return sum(self.allRatings)/float(len(self.allRatings))

    def getAverageDelinquencyRate(self):
        return sum(self.allDelinquencyRates)/float(len(self.allDelinquencyRates))

    def getPartner(self,partnerId):
        return self.dict[partnerId]

    def getMultiplePartnerFeatures(self, partnerId):
        result = self.getPartner(partnerId).getMultipleFeatures()
        for res in result:
            if res[1] is None:
                function = "self.getAverage%s()" % res[0]
                # Replave in place by average value
                res[1] = eval(function)
        return result

if __name__ == "__main__":

    partners = KivaPartners()
    p185 = partners.getPartner(185)
    avgRating = partners.getAverageRating()
    assert(avgRating > 0.0)
    assert(avgRating < 5.0)
    avgDelinquencyRate = partners.getAverageDelinquencyRate()
    assert(avgDelinquencyRate > 0.0)
    assert(avgDelinquencyRate < 100.0)
