# -*- coding:utf-8 -*-

import re, urllib2
from xml.etree.ElementTree import XML
from bs4 import BeautifulSoup
import PyICU
import generator


class Iso4217CodeList(object):

    """ Formato do dicionario:
        * Código da moeda.
        * Datos da moeda. (dicionario)
            * Nome da moeda en inglés.
            * Lista de rexións nas que se usa a moeda, en inglés.

        Exemplo:
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
        currencyCountry = currencyCountry.replace("\n", " ").replace("  ", " ")
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
        for entry in root.find("CcyTbl").findall("CcyNtry"):
            if entry.find("Ccy") is not None:
                self.addEntry(entry.find("Ccy").text, entry.find("CcyNm").text, entry.find("CtryNm").text)

    def toDicFormat(self):
        result = ""
        for currencyCode in sorted(self.codes.iterkeys()):
            result += currencyCode + ( ' '*(10-len(currencyCode)) ) + '# '
            result += ', '.join([currencyName + ' (' + ', '.join(sorted(self.codes[currencyCode][currencyName])) + ')' for currencyName in sorted(self.codes[currencyCode].iterkeys())])
            result += '.\n'
        return result


class Iso4217Generator(generator.Generator):

    def __init__(self):
        self.resource = "iso4217/vocabulario.dic"

    def generateFileContent(self):
        codeList = Iso4217CodeList()
        codeList.loadFromXml(urllib2.urlopen("http://www.currency-iso.org/dam/downloads/table_a1.xml").read())
        return codeList.toDicFormat()



class Iso639CodeList(object):

    """ Format of the dictionary:
        * Language code.
        * Languages represented. (dictionary)
            * Language name, in English.
            * Code tables in which the language code represents the language name. (list)

        Example:
        {
            'aar',
            [
                'Afar',
                ['639-2', '639-3', '639-5']
            ]
        }
    """
    codes = {}

    def __init__(self):
        pass

    def addEntry(self, languageCode, languageName, codeTableName):
        if languageCode not in self.codes:
            self.codes[languageCode] = { languageName: [codeTableName] }
        else:
            if languageName not in self.codes[languageCode]:
                self.codes[languageCode][languageName] = [codeTableName]
            else:
                if codeTableName not in self.codes[languageCode][languageName]:
                    self.codes[languageCode][languageName].append(codeTableName)

    def mergeFromSilOrgPage(self, pageContent):
        soup = BeautifulSoup(pageContent)
        for row in soup.find_all("table")[0].find_all("tr"):
            index = 0
            codesAndTables = []
            languageName = ""
            for column in row.find_all("td")[:4]:
                columnText = column.get_text(" ", strip=True)
                if index < 3:
                    if len(columnText) > 3: # Not a standard entry.
                        if '/' in columnText: # Format: asd / ghj *
                            codesAndTables.append([columnText[0:3], "639-2/T"])
                            codesAndTables.append([columnText[6:9], "639-2/B"])
                        elif "deprecated" in columnText: # Format: asd (deprecated)
                            pass
                        else:
                            raise Exception
                    elif len(columnText) != 0:
                        if index == 0:
                            codesAndTables.append([columnText, "639-3"])
                        elif index == 1:
                            codesAndTables.append([columnText, "639-2/639-5"])
                        elif index == 2:
                            codesAndTables.append([columnText, "639-1"])
                        else:
                            raise Exception
                    else:
                        pass # Empty cell.
                else:
                    if columnText == "Reserved for local use" \
                    or columnText == "Multiple languages" \
                    or columnText == "Undetermined" \
                    or columnText == "No linguistic content":
                        codesAndTables = []
                    else:
                        languageName = columnText
                index += 1
            for codeAndTable in codesAndTables:
                self.addEntry(codeAndTable[0], languageName, codeAndTable[1])

    def toDicFormat(self):
        result = ""
        for languageCode in sorted(self.codes.iterkeys()):
            result += languageCode + ( ' '*(10-len(languageCode)) ) + '# '
            result += ', '.join([representedLanguage + ' (' + ', '.join(sorted(self.codes[languageCode][representedLanguage])) + ')' for representedLanguage in sorted(self.codes[languageCode].iterkeys())])
            result += '.\n'
        return result


class Iso639Generator(generator.Generator):

    def __init__(self):
        self.resource = "iso639/vocabulario.dic"


    def generateFileContent(self):
        codeList = Iso639CodeList()
        codeList.mergeFromSilOrgPage(urllib2.urlopen("http://www-01.sil.org/iso639-3/codes.asp?order=639_3&letter=%25").read())
        return codeList.toDicFormat()



def loadGeneratorList():
    generators = []
    generators.append(Iso4217Generator())
    generators.append(Iso639Generator())
    return generators