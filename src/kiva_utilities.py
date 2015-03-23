def countGender(people):
    result = {u'M':0,
              u'F':0}
    for person in people:
        result[person[u'gender']] += 1
    return result

def getMajorityGender(people):
    result = ""
    genders = countGender(people)
    nrMales = genders[u'M']
    nrFemales = genders[u'F']
    if nrMales > nrFemales:
        return u'M'
    elif nrFemales > nrMales:
        return u'F'
    else:
        return u'N'    

def getFundingRatio(numerator, denominator, numberOfBins):
    '''
    This very ad-hoc function calculates a ratio and assigns the ratio in numberOfBins evenly-spaced
    bins (named 0 through numberOfBins-1), OR in bin numberOfBins.
    What's special, is that the bin numberOfBins is chosen IFF ratio >= 1
    Bins 0 through numberOfBins-1 are closed-ended on their lower side,
    and open-ended on their larger side.
    '''
    assert(numerator >= 0.0)
    assert(denominator >= 0.0)
    assert(numberOfBins >= 2)
    assert(type(numberOfBins) == type(1)) # i.e. int
    ratio = float(numerator)/float(denominator)
    assert(ratio >= 0.0)
    if ratio >= 1.0:
        return numberOfBins
    else:
        binWidth = 1/float(numberOfBins)
        for binCounter in range(numberOfBins):
            if ratio < binWidth * (binCounter+1):
                return binCounter

if __name__ == "__main__":
    
    borrowers1 = [{u'gender': u'F', u'first_name': u'Perla Cristina ', u'last_name': u'', u'pictured': True}, {u'gender': u'F', u'first_name': u'Escarleth Del Carmen ', u'last_name': u'', u'pictured': True}, {u'gender': u'M', u'first_name': u'Jos\xe9 Evelio ', u'last_name': u'', u'pictured': True}]
    assert(countGender(borrowers1)[u'F'] == 2)
    assert(countGender(borrowers1)[u'M'] == 1)
    assert(getMajorityGender(borrowers1) == u'F')

    borrowers2 = [{u'gender': u'F', u'first_name': u'Perla Cristina ', u'last_name': u'', u'pictured': True}, {u'gender': u'M', u'first_name': u'Jos\xe9 Evelio ', u'last_name': u'', u'pictured': True}]
    assert(countGender(borrowers2)[u'F'] == 1)
    assert(countGender(borrowers2)[u'M'] == 1)
    assert(getMajorityGender(borrowers2) == u'N')

    borrowers3 = [{u'gender': u'M', u'first_name': u'Jos\xe9 Evelio ', u'last_name': u'', u'pictured': True}]
    assert(countGender(borrowers3)[u'F'] == 0)
    assert(countGender(borrowers3)[u'M'] == 1)
    assert(getMajorityGender(borrowers3) == u'M')

    borrowers4 = []
    assert(countGender(borrowers4)[u'F'] == 0)
    assert(countGender(borrowers4)[u'M'] == 0)
    assert(getMajorityGender(borrowers4) == u'N')

    assert(getFundingRatio(0, 1000, 4) == 0)
    assert(getFundingRatio(3, 10, 2) == 0)
    assert(getFundingRatio(7, 10, 2) == 1)
    assert(getFundingRatio(10, 10, 2) == 2)
    assert(getFundingRatio(3, 10, 10) == 2)
    assert(getFundingRatio(9.5, 10, 10) == 9)
    assert(getFundingRatio(10, 10, 10) == 10)
