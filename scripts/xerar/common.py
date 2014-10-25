# -*- coding:utf-8 -*-

from __future__ import print_function

import os, pickle, re, requests, sys, time, urllib
from datetime import datetime, timedelta
from xdg.BaseDirectory import save_cache_path
import PyICU

from generator import output, wordsToIgnore



numberPattern = re.compile(u"^[0-9-]*[0-9]+(\.?[ºª]|[.°:])?$")


def getModulesSourcePath():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)).decode("utf-8"), u"../../src")



class CacheManager(object):

    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CacheManager, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance


    def __init__(self):
        self.cacheFolder = save_cache_path(u"hunspell-gl")
        self.pickleFolder = os.path.join(self.cacheFolder, u"pickle")


    def cachePath(self, resourcePath, objectName):
        return os.path.join(self.pickleFolder, resourcePath, objectName)


    def exists(self, resourcePath, objectName):
        cachePath = self.cachePath(resourcePath, objectName)
        if not os.path.exists(cachePath):
            return False
        fileData = os.stat(cachePath)
        if (time.time() - fileData.st_mtime) > 86400: # Older than 24h.
            return False
        return True


    def load(self, resourcePath, objectName):
        cachePath = self.cachePath(resourcePath, objectName)
        with open(cachePath, "r") as fileObject:
            return pickle.load(fileObject)


    def save(self, resourcePath, objectName, objectData):
        cachePath = self.cachePath(resourcePath, objectName)
        if not os.path.exists(os.path.dirname(cachePath)):
            os.makedirs(os.path.dirname(cachePath))
        with open(cachePath, "w") as fileObject:
            pickle.dump(objectData, fileObject)


# Progress reporters.

class ProgressReporter(object):

    def report(self):
        output(u"{}→ {}… {}/{} ({}%)\r".format(
            u" "*self.indent,
            self.statement,
            self.processed,
            self.total,
            self.processed*100/self.total,
        ))


    def __init__(self, statement, total, indent=0):
        self.statement = statement
        self.total = total
        self.indent = indent
        self.processed = 0
        if self.total:
            self.report()

    def increase(self, count=1):
        self.processed += count
        self.report()

    def done(self):
        if self.total:
            output(u"{}✓ {}. {}/{} ({}%)\n".format(
                u" "*self.indent,
                self.statement,
                self.processed,
                self.total,
                self.processed*100/self.total,
            ))


class TaskInProgressReporter(object):

    def report(self):
        output(u"{}→ {}…\r".format(u" "*self.indent, self.statement))


    def __init__(self, statement, indent=0):
        self.statement = statement
        self.indent = indent
        self.report()


    def done(self):
        output(u"{}✓ {}.\n".format(u" "*self.indent, self.statement))



def formatEntriesForDictionary(entries, partOfSpeech):
    return formatEntriesAndCommentsForDictionary(dict.fromkeys(entries, None), partOfSpeech)



def escapeSpecialEntryCharacters(entry):
    return entry.replace("/", "\/")


def formatEntriesAndCommentsForDictionary(entries, partOfSpeech):
    reporter = ProgressReporter(u"Adaptando as entradas ao formato do dicionario", len(entries))
    collator = PyICU.Collator.createInstance(PyICU.Locale('gl.UTF-8'))
    for entry in sorted(entries, cmp=collator.compare):
        if " " in entry: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
            ngramas = set()
            for ngrama in entry.split(u" "):
                ngrama = ngrama.strip(",")
                if ngrama == u"/": # e.g. «Alianza 90 / Os Verdes».
                    continue
                if ngrama not in wordsToIgnore:  # N-gramas innecesarios por ser vocabulario galego xeral.
                    if ngrama not in ngramas:  # Non é necesario repetir ngramas dentro da mesma entrada
                        if not numberPattern.match(ngrama):  # Hunspell sempre acepta números.
                            ngramas.add(ngrama)
                            if entries[entry]: # A entrada ten comentario.
                                yield u"{ngrama} po:{partOfSpeech} [n-grama: {entry}]  # {comment}\n".format(ngrama=escapeSpecialEntryCharacters(ngrama), entry=entry, partOfSpeech=partOfSpeech, comment=entries[entry])
                            else:
                                yield u"{ngrama} po:{partOfSpeech} [n-grama: {entry}]\n".format(ngrama=escapeSpecialEntryCharacters(ngrama), entry=entry, partOfSpeech=partOfSpeech)
        else:
            if entry not in wordsToIgnore and not numberPattern.match(entry):  # Hunspell sempre acepta números.
                if entries[entry]: # A entrada ten comentario.
                    yield u"{entry} po:{partOfSpeech}  # {comment}\n".format(entry=escapeSpecialEntryCharacters(entry), partOfSpeech=partOfSpeech, comment=entries[entry])
                else:
                    yield u"{entry} po:{partOfSpeech}\n".format(entry=escapeSpecialEntryCharacters(entry), partOfSpeech=partOfSpeech)
        reporter.increase()
    reporter.done()



class ContentCache(object):

    def __init__(self, cacheFolder):

        cacheManager = CacheManager()
        self.cacheFolder = os.path.join(cacheManager.cacheFolder, cacheFolder)
        if not os.path.exists(self.cacheFolder):
            os.makedirs(self.cacheFolder)


    def downloadFileIfNeededAndGetLocalPath(self, url, fileName=None):

        if not fileName:
            fileName = url.split(u"/")[-1]
        localPath = os.path.join(self.cacheFolder, fileName)

        if not os.path.exists(localPath):
            urllib.urlretrieve(url, localPath)
            return localPath

        request = requests.head(url)
        localFileDate = datetime.strptime(time.ctime(os.path.getmtime(localPath)), "%a %b %d %H:%M:%S %Y")

        # Cache for at least 24 hours. This is specially important for URLs that do not provide a
        # last modified time.
        yesterday = datetime.now() - timedelta(days=1)
        if localFileDate >= yesterday:
            return localPath

        lastModified = request.headers.get("Last-Modified")
        if lastModified:
            remoteFileDate = datetime.strptime(lastModified, '%a, %d %b %Y %H:%M:%S GMT')
            if localFileDate >= remoteFileDate:
                return localPath

        urllib.urlretrieve(url, localPath)
        return localPath



class PdfParser(object):

    def __init__(self, filePath):
        self.filePath = filePath


    def lines(self):

        from pdfminer.layout import LAParams, LTChar
        from pdfminer.pdfparser import PDFParser
        from pdfminer.pdfdocument import PDFDocument
        from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
        from pdfminer.converter import PDFPageAggregator
        from pdfminer.pdfpage import PDFPage

        fileObject = open(self.filePath, "rb")
        parser = PDFParser(fileObject)
        document = PDFDocument(parser)
        resourceManager = PDFResourceManager()
        device = PDFPageAggregator(resourceManager)
        interpreter = PDFPageInterpreter(resourceManager, device)
        for page in PDFPage.create_pages(document):
            interpreter.process_page(page)
            layout = device.get_result()
            objects = [object for object in layout if isinstance(object, LTChar)]
            if objects:
                params = LAParams()
                for line in layout.group_objects(params, objects):
                    yield line.get_text()
