# -*- coding:utf-8 -*-

import codecs, urllib2
from xml.etree.ElementTree import XML


class CodeList(object):

    """ Format of the dictionary:
        * Currency code.
        * Currency data. (dictionary)
            * Currency name, in English.
            * Regions where the currency is used. (list)

        Example:
        {
            'EUR',
            [
                'Euro',
                ['ÅLAND ISLANDS', 'ANDORRA', 'AUSTRIA', …]
            ]
        }
    """
    codes = {}

    def __init__(self):
        pass

    def addEntry(self, currencyCode, currencyName, currencyCountry):
        if currencyCode not in self.codes:
            self.codes[currencyCode] = { currencyName: [currencyCountry] }
        else:
            if currencyName not in self.codes[currencyCode]:
                self.codes[currencyCode][currencyName] = [currencyCountry]
            else:
                if currencyCountry not in self.codes[currencyCode][currencyName]:
                    self.codes[currencyCode][currencyName].append(currencyCountry)

    def loadFromXml(self, xmlContent):
        root = XML(xmlContent)
        for entry in root.findall("ISO_CURRENCY"):
            fields = list(entry)
            if fields[2].text is not None:
                self.addEntry(fields[2].text, fields[1].text, fields[0].text)

    def toDicFormat(self):
        result = ""
        for currencyCode in sorted(self.codes.iterkeys()):
            result += currencyCode + ( ' '*(10-len(currencyCode)) ) + '# '
            result += ', '.join([currencyName + ' (' + ', '.join(sorted(self.codes[currencyCode][currencyName])) + ')' for currencyName in sorted(self.codes[currencyCode].iterkeys())])
            result += '.\n'
        return result


def getCurrencyCodesDictionary():
    codeList = CodeList()
    codeList.loadFromXml(urllib2.urlopen("http://www.currency-iso.org/dam/isocy/downloads/dl_iso_table_a1.xml").read())
    return codeList


def main():
    codeList = getCurrencyCodesDictionary()
    dic = codeList.toDicFormat()
    with codecs.open('iso4217.dic', 'w', 'utf-8') as f:
        f.write(dic)

main()
