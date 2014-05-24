# -*- coding:utf-8 -*-

import textwrap

import codecs

from common import formatEntriesAndCommentsForDictionary, ContentCache, PdfParser
import generator



contentCache = ContentCache("microsoft")
styleGuidePdfUrl = u"http://download.microsoft.com/download/D/7/2/D72521AC-634E-41B1-8431-6F75C29CAE84/glg-esp-StyleGuide.pdf"


class AbbreviationsGenerator(generator.Generator):

    def __init__(self):
        self.resource = u"microsoft/abreviaturas.dic"


    def parseSubEntries(self, entry):
        if u" / " in entry:
            for subentry in entry.split(u" / "):
                yield subentry
        else:
            yield entry


    def generateFileContent(self):

        filePath = contentCache.downloadFileIfNeededAndGetLocalPath(styleGuidePdfUrl)
        pdfParser = PdfParser(filePath)

        entries = {}
        parsingStage = 0
        previousLine = u""

        for line in pdfParser.lines():

            line = line.strip()

            if parsingStage == 0:
                if line == u"List of common abbreviations:":
                    parsingStage += 1
                else:
                    continue

            elif parsingStage == 1:
                if line == u"Addtional guidelines:":
                    break

            # Yes, I know, ugliest decoding ever… It looks like different parts
            # of the PDF use different encoding, so… bare with me.
            line = line.replace(u"ñ", u"ó").replace(u"ð", u"ñ").replace(u"ö", u"ú")

            if line.startswith(u"(+)"):
                comment = previousLine
                entry = line[3:].strip()
                for subentry in self.parseSubEntries(entry):
                    subentry = subentry.strip()
                    entries[subentry] = comment.strip()

            previousLine = line

        dictionary  = u"# Relación de abreviaturas máis frecuentes\n"
        dictionary += u"# {}\n".format(styleGuidePdfUrl)
        dictionary += u"\n"
        for entry in formatEntriesAndCommentsForDictionary(entries, u"abreviatura"):
            dictionary += entry
        return dictionary


def loadGeneratorList():
    generators = []
    generators.append(AbbreviationsGenerator())
    return generators