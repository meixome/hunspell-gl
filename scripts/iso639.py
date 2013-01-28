# -*- coding:utf-8 -*-

import codecs, urllib2
from bs4 import BeautifulSoup


class CodeList(object):

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


def getSilOrgPageForLetter(letter):
    return urllib2.urlopen("http://www.sil.org/iso639-3/codes.asp?order=639_3&letter={letter}".format(letter=letter)).read()


def getLatinAlphabet():
    return ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']


def getLanguageCodesDictionary():
    codeList = CodeList()
    for letter in getLatinAlphabet():
        codeList.mergeFromSilOrgPage(getSilOrgPageForLetter(letter))
    return codeList


def main():
    codeList = getLanguageCodesDictionary()
    dic = codeList.toDicFormat()
    with codecs.open('iso639.dic', 'w', 'utf-8') as f:
        f.write(dic)

main()
