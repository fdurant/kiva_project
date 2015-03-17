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
