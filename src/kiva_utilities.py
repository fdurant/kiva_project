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

def getFundingRatioLabel(numerator, denominator, posCutoff=1.0, negCutoff=0.5):
    '''
    This very ad-hoc function calculates the funding ratio and returns a label based on its value
    Possible return values are:
    -1: to be discarded
    0: not funded
    1: funded
    '''
    assert(numerator >= 0.0)
    assert(denominator >= 0.0)
    assert(posCutoff > negCutoff)
    ratio = float(numerator)/float(denominator)
    assert(ratio >= 0.0)
    if ratio >= posCutoff:
        return 1
    elif ratio <= negCutoff:
        return 0
    else:
        return -1

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

    assert(getFundingRatioLabel(0, 10) == 0)
    assert(getFundingRatioLabel(10, 10) == 1)
    assert(getFundingRatioLabel(1, 2) == 0)
    assert(getFundingRatioLabel(2, 3) == -1)
    assert(getFundingRatioLabel(2, 4) == 0)
    assert(getFundingRatioLabel(3, 10, negCutoff=0.3) == 0)
    assert(getFundingRatioLabel(3, 10, negCutoff=0.2) == -1)
    assert(getFundingRatioLabel(3, 10, negCutoff=0.3) == 0)
    assert(getFundingRatioLabel(8, 10, posCutoff=0.8) == 1)
    assert(getFundingRatioLabel(8, 10, posCutoff=0.9) == -1)
