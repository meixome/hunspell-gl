# -*- coding:utf-8 -*-

import textwrap

import codecs

from common import formatEntriesAndCommentsForDictionary, ContentCache, PdfParser
import generator



contentCache = ContentCache("udc")
abbreviationsPdfUrl = u"http://download.microsoft.com/download/A/0/B/A0B1A66A-5EBF-4CF3-9453-4B13BB027F1F/Phd_thesis_DB_v21.pdf"
languageUsageCriteria2012PdfUrl = u"http://www.udc.es/snl/documentospdf/Libro_Criterios_lingua.pdf"
languageUsageCriteria2007PdfUrl = u"http://www.concellodezas.org/linguazas/documentos/criterios_uso_lingua.pdf"


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

        filePath = contentCache.downloadFileIfNeededAndGetLocalPath(languageUsageCriteria2012PdfUrl)
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

        dictionary  = u"# Relación de abreviaturas máis frecuentes na linguaxe administrativa\n"
        dictionary += u"# {}\n".format(languageUsageCriteria2012PdfUrl)
        dictionary += u"\n"
        for entry in formatEntriesAndCommentsForDictionary(entries, u"abreviatura"):
            dictionary += entry
        return dictionary


class TitleAbbreviationsGenerator(generator.Generator):

    def __init__(self):
        self.resource = u"udc/abreviaturas/tratamento.dic"


    def generateFileContent(self):

        filePath = contentCache.downloadFileIfNeededAndGetLocalPath(languageUsageCriteria2007PdfUrl)
        pdfParser = PdfParser(filePath)

        entries = {}
        parsingStage = 0
        comment = None
        entry = None
        twoLines = 0

        for line in pdfParser.lines():

            line = line.strip()
            if not line:
                continue

            if parsingStage == 0:
                if line == u"ABREVIATURAS DE TRATAMENTO":
                    parsingStage += 1
                continue

            elif parsingStage == 1:
                if line == u"CRITERIOS PARA O USO DA LINGUA":
                    break

            if line.isdigit():
                continue

            if twoLines != 0:
                if twoLines == 1:
                    entry = line
                    twoLines += 1
                    continue
                elif twoLines == 2:
                    comment = comment[:-1] + line
                    twoLines += 1
                    continue
                elif twoLines == 3:
                    entry += u" " + line
                    twoLines = 0

            if not comment:
                comment = line
                if comment.endswith(u"-"):
                    twoLines = 1
                continue
            else:
                if not entry:
                    entry = line
                entries[entry] = comment
                comment = None
                entry = None


        dictionary  = u"# Relación de abreviaturas de tratamento\n"
        dictionary += u"# {}\n".format(languageUsageCriteria2007PdfUrl)
        dictionary += u"\n"
        for entry in formatEntriesAndCommentsForDictionary(entries, u"abreviatura"):
            dictionary += entry
        return dictionary


class AcronymsGenerator(generator.Generator):

    def __init__(self):
        self.resource = u"udc/siglas/xeral.dic"


    def generateFileContent(self):

        filePath = contentCache.downloadFileIfNeededAndGetLocalPath(languageUsageCriteria2012PdfUrl)
        pdfParser = PdfParser(filePath)

        entries = {}
        parsingStage = 0
        entry = None
        twoLineEntries = [u"CGENDL", u"CIXTEC", u"CORDIS", u"ECTS", u"EFQM", u"FAO", u"ISBN", u"ISO", u"ISSN", u"Unesco", "Unicef"]

        for line in pdfParser.lines():

            line = line.strip()

            if parsingStage == 0:
                if line == u"ANEXO IV. RELACIÓN DE SIGLAS E ACRÓNIMOS MÁIS HABITUAIS":
                    parsingStage += 1
                continue

            elif parsingStage == 1:
                if line == u"ANEXO V. RELACIÓN DE SIGLAS E ACRÓNIMOS MÁIS HABITUAIS DA UDC":
                    break

            if line in [u"CRITERIOS PARA O USO DA LINGUA", u"ANEXO IV. RELACIÓN DE SIGLAS E ACRÓNIMOS MÁIS HABITUAIS"]:
                continue
            if line.isdigit():
                continue

            if not entry:
                entry = line.strip()
            elif entry in twoLineEntries: # Caso especial que hai que xestionar como malamente se poida.
                if entry in entries:
                    entries[entry] += u" " + line.strip()
                    entry = None
                else:
                    entries[entry] = line.strip()
            else:
                entries[entry] = line.strip()
                entry = None

        dictionary  = u"# Relación de siglas e acrónimos máis frecuentes\n"
        dictionary += u"# {}\n".format(languageUsageCriteria2012PdfUrl)
        dictionary += u"\n"
        for entry in formatEntriesAndCommentsForDictionary(entries, u"sigla"):
            dictionary += entry
        return dictionary


class UdcAcronymsGenerator(generator.Generator):

    def __init__(self):
        self.resource = u"udc/siglas/udc.dic"


    def generateFileContent(self):

        filePath = contentCache.downloadFileIfNeededAndGetLocalPath(languageUsageCriteria2012PdfUrl)
        pdfParser = PdfParser(filePath)

        entries = {}
        parsingStage = 0
        entry = None
        twoLineEntries = [u"ASISTA",]

        for line in pdfParser.lines():

            line = line.strip()

            if parsingStage == 0:
                if line == u"ANEXO V. RELACIÓN DE SIGLAS E ACRÓNIMOS MÁIS HABITUAIS DA UDC":
                    parsingStage += 1
                continue

            elif parsingStage == 1:
                if line.startswith(u"ÚLTIMAS PUBLICACIÓNS"):
                    break

            if line in [u"CRITERIOS PARA O USO DA LINGUA", u"ANEXO V. RELACIÓN DE SIGLAS E ACRÓNIMOS MÁIS HABITUAIS DA UDC"]:
                continue
            if line.isdigit():
                continue

            if not entry:
                entry = line.strip()
            elif entry in twoLineEntries: # Caso especial que hai que xestionar como malamente se poida.
                if entry in entries:
                    entries[entry] += u" " + line.strip()
                    entry = None
                else:
                    entries[entry] = line.strip()
            else:
                entries[entry] = line.strip()
                entry = None

        dictionary  = u"# Relación de siglas e acrónimos máis frecuentes na UDC\n"
        dictionary += u"# {}\n".format(languageUsageCriteria2012PdfUrl)
        dictionary += u"\n"
        for entry in formatEntriesAndCommentsForDictionary(entries, u"sigla"):
            dictionary += entry
        return dictionary


def loadGeneratorList():
    generators = []
    generators.append(AcronymsGenerator())
    generators.append(AbbreviationsGenerator())
    generators.append(AdministrativeAbbreviationsGenerator())
    generators.append(TitleAbbreviationsGenerator())
    generators.append(UdcAcronymsGenerator())
    return generators