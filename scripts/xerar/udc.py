# -*- coding:utf-8 -*-

import textwrap

import codecs

from common import formatEntriesAndCommentsForDictionary, ContentCache, PdfParser
import generator



contentCache = ContentCache("udc")
pdfUrl = u"http://download.microsoft.com/download/A/0/B/A0B1A66A-5EBF-4CF3-9453-4B13BB027F1F/Phd_thesis_DB_v21.pdf"


class AbbreviationsGenerator(generator.Generator):

    def __init__(self):
        self.resource = u"udc/abreviaturas.dic"


    def generateFileContent(self):

        filePath = contentCache.downloadFileIfNeededAndGetLocalPath(pdfUrl)
        pdfParser = PdfParser(filePath)

        entries = {}
        parsingStage = 0
        entry = None

        for line in pdfParser.lines():

            line = line.strip()

            if parsingStage == 0:
                if line == u"Tabela 24: Abreviaturas e sua expansão em galego.":
                    parsingStage += 1
                continue

            elif parsingStage == 1:
                if line == u"Abreviatura":
                    continue
                elif line == u"Conversão ortográfica":
                    continue
                elif line == u"54":
                    break

            if not entry:
                entry = line.strip().replace(u"..", u".")
            elif entry == u"s.a.": # Caso especial que hai que xestionar como malamente se poida.
                if line == u"especificar":
                    entries[entry] += u" " + line.strip()
                    entry = None
                else:
                    entries[entry] = line.strip()
            else:
                entries[entry] = line.strip()
                entry = None

        dictionary  = u"# Relación de abreviaturas máis frecuentes\n"
        dictionary += u"# {}\n".format(pdfUrl)
        dictionary += u"\n"
        for entry in formatEntriesAndCommentsForDictionary(entries, u"abreviatura"):
            dictionary += entry
        return dictionary


def loadGeneratorList():
    generators = []
    generators.append(AbbreviationsGenerator())
    return generators