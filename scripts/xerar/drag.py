# -*- coding:utf-8 -*-

import textwrap

from pdfminer.layout import LAParams, LTCurve, LTRect
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfpage import PDFPage
import codecs

from common import formatEntriesForDictionary
import generator



class AbbreviationsGenerator(generator.Generator):

    def __init__(self):
        self.resource = "rag/gl/abreviaturas.dic"


    def generateFileContent(self):

        import tempfile
        import urllib

        abbreviationsPdfUrl = u"http://www.realacademiagalega.org/c/document_library/get_file?uuid=f29e6ce1-9ac5-42e3-8c15-73c4b9b5f48b&groupId=10157"
        temporaryFile = tempfile.NamedTemporaryFile()
        urllib.urlretrieve(abbreviationsPdfUrl, temporaryFile.name)

        entries = set()
        fileObject = open(temporaryFile.name, "rb")
        parser = PDFParser(fileObject)
        document = PDFDocument(parser)
        resourceManager = PDFResourceManager()
        device = PDFPageAggregator(resourceManager)
        interpreter = PDFPageInterpreter(resourceManager, device)
        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            layout = device.get_result()
            objects = [object for object in layout if not isinstance(object, LTRect) and not isinstance(object, LTCurve)]
            params = LAParams()
            for line in layout.group_objects(params, objects):
                text = line.get_text()
                if u":" in text:
                    entry = text.split(u":")[0]
                    entry = entry.strip()
                    entry = entry.replace(u"..", ".")
                    entries.add(entry)

        dictionary  = u"# Abreviaturas empregadas no Dicionario da Real Academia Galega\n"
        dictionary += u"# http://www.realacademiagalega.org/abreviaturas\n"
        dictionary += u"\n"
        for entry in formatEntriesForDictionary(entries, u"abreviatura"):
            dictionary += entry
        return dictionary


def loadGeneratorList():
    generators = []
    generators.append(AbbreviationsGenerator())
    return generators