import re
import langid
import codecs
import sys

# Borrowed from http://farmdev.com/talks/unicode/
def to_unicode_or_bust(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

def removeHtmlTags(text):
    tagPattern = re.compile("(<\/?[^>]*?>)")
    result = re.sub(tagPattern, '', text)
    return result

def getTranslations(desc):
    '''
    Splits the possibly multilingual (because translated) text in two pieces and identifies their respective language.

    Returns a list of tuples, each tuple consisting of the detected language code and the piece that was separated
    '''

    assert(isinstance(desc,unicode)), "desc is not unicode"

    result = []

    # Split on the boilerplate sentence
    splitPattern = u"[tT]ranslated\s+from\s+\S+\s+by.+Kiva\s+[Vv]olunteer\.?"
    pieces = re.split(splitPattern, desc)
    
    for p in pieces:
        langcode = langid.classify(p)
        result.append((langcode,removeHtmlTags(p)))

    return result
        
def identifyLanguagePerParagraph(desc):
    '''
    This function splits the desc into paragraphs (using very simple means) and returns a list
    of tuples containing a language code and the paragraph itself
    
    '''

    assert(isinstance(desc,unicode)), "desc is not unicode"

    result = []

    # Split on paragraph boundary
    splitPattern = "[\r\n]{2,}"
    paragraphs = re.split(splitPattern, desc)

    for p in paragraphs:
        langcode = to_unicode_or_bust(langid.classify(p)[0])
        result.append((langcode,removeHtmlTags(p)))

    return result

if __name__ == "__main__":

    assert(removeHtmlTags("<a href=\"http://www.somesite.com/\">This is a link</a>") == "This is a link")
    assert(removeHtmlTags("<p><b>That's a bold statement!</b></p>") == "That's a bold statement!")

    desc1 = u"Born in 1967 in Lom\u00e9, Mrs. Latifa A. is married and the mother of two (02) children.  She owns a  grocery store that is successful.  With her income she manages to contribute to the family\u2019s needs. Very ambitious, she would like to have a second store in another neighborhood.  She is requesting a loan of $600 to stock up the shop,particularly for this year-end period when sales increase.<p>\r\n<p><b>Translated from French by V\u00e9ronique Fourment, Kiva volunteer.<\/b><p>\r\n\r\nN\u00e9e en 1967 \u00e0 Lom\u00e9, Madame Latifa A. est mari\u00e9e et m\u00e8re de deux (02) enfants. Elle d\u00e9tient une boutique d\u2019alimentation g\u00e9n\u00e9rale qui lui r\u00e9ussit bien. Avec ses revenus, elle arrive \u00e0 contribuer aux charges de sa famille. Tr\u00e8s ambitieuse, elle veut avoir une seconde boutique dans un autre quartier mais. Elle sollicite un cr\u00e9dit de $600 pour approvisionner sa boutique surtout en ses p\u00e9riodes de fin d\u2019ann\u00e9e o\u00f9 la vente augmente.<p>"

    paragraphs1 = identifyLanguagePerParagraph(desc1)
    for p in paragraphs1:
        print "detected language is: ", p[0]
        print p[1].encode('utf-8')
