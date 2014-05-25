# -*- coding:utf-8 -*-

import textwrap

import codecs

from common import formatEntriesAndCommentsForDictionary, ContentCache, PdfParser
import generator



contentCache = ContentCache("udc")
abbreviationsPdfUrl = u"http://download.microsoft.com/download/A/0/B/A0B1A66A-5EBF-4CF3-9453-4B13BB027F1F/Phd_thesis_DB_v21.pdf"
administrativeAbbreviationsPdfUrl = u"http://www.udc.es/snl/documentospdf/Libro_Criterios_lingua.pdf"


class AbbreviationsGenerator(generator.Generator):

    def __init__(self):
        self.resource = u"udc/abreviaturas/xeral.dic"


    def generateFileContent(self):

        filePath = contentCache.downloadFileIfNeededAndGetLocalPath(abbreviationsPdfUrl)
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
        dictionary += u"# {}\n".format(abbreviationsPdfUrl)
        dictionary += u"\n"
        for entry in formatEntriesAndCommentsForDictionary(entries, u"abreviatura"):
            dictionary += entry
        return dictionary


class AdministrativeAbbreviationsGenerator(generator.Generator):

    def __init__(self):
        self.resource = u"udc/abreviaturas/administración.dic"


    def generateFileContent(self):

        filePath = contentCache.downloadFileIfNeededAndGetLocalPath(administrativeAbbreviationsPdfUrl)
        pdfParser = PdfParser(filePath)

        entries = {}
        parsingStage = 0
        comment = None

        import string

        for line in pdfParser.lines():

            line = line.strip()

            if parsingStage == 0:
                if line == u"ANEXO I. ABREVIATURAS MÁIS EMPREGADAS NA LINGUAXE ADMINISTRATIVA":
                    parsingStage += 1
                continue

            elif parsingStage == 1:
                if line.startswith("5"):
                    parsingStage += 1
                    continue

            elif parsingStage == 2:
                if line == u"ANEXO I. ABREVIATURAS MÁIS EMPREGADAS NA LINGUAXE ADMINISTRATIVA":
                    parsingStage += 1
                else:
                    continue

            elif parsingStage == 3:
                if line == u"ANEXO II. RELACIÓN DOS TOPÓNIMOS MÁIS HABITUAIS DE FÓRA DO ESTADO ESPAÑOL":
                    break

            if line in string.uppercase:
                continue
            if line in [u"CRITERIOS PARA O USO DA LINGUA", u"ANEXO I. ABREVIATURAS MÁIS EMPREGADAS NA LINGUAXE ADMINISTRATIVA"]:
                continue
            if line.isdigit():
                continue

            if not comment:
                comment = line.strip()
            else:
                entries[line.strip()] = comment
                comment = None

        dictionary  = u"# Relación de abreviaturas máis frecuentes\n"
        dictionary += u"# {}\n".format(administrativeAbbreviationsPdfUrl)
        dictionary += u"\n"
        for entry in formatEntriesAndCommentsForDictionary(entries, u"abreviatura"):
            dictionary += entry
        return dictionary


def loadGeneratorList():
    generators = []
    generators.append(AbbreviationsGenerator())
    generators.append(AdministrativeAbbreviationsGenerator())
    return generators