# -*- coding:utf-8 -*-

import os, re, requests, sys, tempfile, time, unicodedata, urllib, urllib2

import PyICU
from bs4 import BeautifulSoup

import pywikibot
from pywikibot.xmlreader import XmlDump

from common import CacheManager
from generator import Generator, output, wordsToIgnore



fileTagPattern = re.compile(u"(?i)\[\[ *(File|Image|Ficheiro|Imaxe):([^][]|\[\[[^][]+\]\])+\]\] *")
htmlStartTagPattern = re.compile(u"< *(\w+)[^>]*?(?<!/)>")
htmlEndTagPattern = re.compile(u"</ *(\w+) *>")
tagsToSkip = [u"br", "hr"]
tableStartTagPattern = re.compile(u"(?<!\{)\{\|")
tableEndTagPattern = re.compile(u"\|\}(?!\})")
fileStartTagPattern = re.compile(u"(?i)\[\[ *(File|Image|Ficheiro|Imaxe):")

boldPattern = re.compile(u"\'\'\' *(.*?) *\'\'\'")
parenthesis = re.compile(u" *\([^)]*\)")
reference = re.compile(u"< *ref[^>]*>.*?< */ *ref *>")
wikiTags = re.compile(u"\[\[|\]\]")
sentenceSeparatorPattern = re.compile(u"(?<!(a\.C|d\.C|.St))\. ")



# Helpers.

_regexType = type(re.compile(u"."))

def parsePattern(pattern):
    if not pattern:
        return pattern
    if not isinstance(pattern, _regexType):
        pattern = re.compile(pattern)
    return pattern


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



# Dictionary generators.

numberPattern = re.compile(u"^[0-9]+$")

class MediaWikiGenerator(Generator):


    def __init__(self, siteName, languageCode, resource, partOfSpeech, entryGenerators):

        self.resource = u"{}/{}/{}".format(siteName, languageCode, resource)
        self.partOfSpeech = partOfSpeech

        site = pywikibot.Site(languageCode, siteName)
        for entryGenerator in entryGenerators:
            entryGenerator.setSite(site)
        self.entryGenerators = entryGenerators


    def formatEntriesForDictionary(self, entries, partOfSpeech):
        reporter = ProgressReporter(u"Adaptando as entradas ao formato do dicionario", len(entries))
        collator = PyICU.Collator.createInstance(PyICU.Locale('gl.UTF-8'))
        for entry in sorted(entries, cmp=collator.compare):
            if " " in entry: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
                ngramas = set()
                for ngrama in entry.split(u" "):
                    ngrama = ngrama.strip(",")
                    if ngrama not in wordsToIgnore:  # N-gramas innecesarios por ser vocabulario galego xeral.
                        if ngrama not in ngramas:  # Non é necesario repetir ngramas dentro da mesma entrada
                            if not numberPattern.match(ngrama):  # Hunspell sempre acepta números.
                                ngramas.add(ngrama)
                                yield u"{ngrama} po:{partOfSpeech} [n-grama: {entry}]\n".format(ngrama=ngrama, entry=entry, partOfSpeech=partOfSpeech)
            else:
                if entry not in wordsToIgnore:
                    yield u"{entry} po:{partOfSpeech}\n".format(entry=entry, partOfSpeech=partOfSpeech)
            reporter.increase()
        reporter.done()


    def generateFileContent(self):

        # No-cache parameters parsing.
        #
        # -nocache
        # -nocache:pageGenerators
        # -nocache:pageParser
        # -nocache:entryParser
        #
        # Each no-cache parameter implies the ones below. For example,
        # -nocache:pageGenerators implies -nocache:pageParser and
        # -nocache:entryParser as well.
        noCacheSet = set()
        if "-nocache" in sys.argv or "-nocache:pageGenerators" in sys.argv:
            noCacheSet.add(u"pageGenerators")
            noCacheSet.add(u"pageParser")
            noCacheSet.add(u"entryParser")
        elif "-nocache:pageParser" in sys.argv:
            noCacheSet.add(u"pageParser")
            noCacheSet.add(u"entryParser")
        elif "-nocache:entryParser" in sys.argv:
            noCacheSet.add(u"entryParser")

        cacheManager = CacheManager()

        totalEntries = set()

        index = 1
        for entryGenerator in self.entryGenerators:

            # Obtaining a list of pages to parse.
            cacheName = u"pageNames" + unicode(index)
            if u"pageGenerators" not in noCacheSet and cacheManager.exists(self.resource, cacheName):
                pages = [pywikibot.Page(entryGenerator.site, pageName) for pageName in cacheManager.load(self.resource, cacheName)]
            else:
                pages = set()
                for pageGenerator in entryGenerator.pageGenerators:
                    for page in pageGenerator.run():
                        pages.add(page)
                cacheManager.save(self.resource, cacheName, [page.title() for page in pages])

            # Parsing the pages to obtain a list of entries.
            cacheName = u"entries" + unicode(index)
            if u"pageParser" not in noCacheSet and cacheManager.exists(self.resource, cacheName):
                entries = cacheManager.load(self.resource, cacheName)
            else:
                entries = set()
                for entry in entryGenerator.pageParser.parse(pages):
                    entries.add(entry)
                cacheManager.save(self.resource, cacheName, entries)

            # Parsing the entries.
            cacheName = u"parsedEntries" + unicode(index)
            if u"entryParser" not in noCacheSet and cacheManager.exists(self.resource, cacheName):
                parsedEntries = cacheManager.load(self.resource, cacheName)
            else:
                parsedEntries = set()
                for parsedEntry in entryGenerator.entryParser.parse(entries):
                    parsedEntries.add(parsedEntry)
                cacheManager.save(self.resource, cacheName, parsedEntries)

            totalEntries.update(parsedEntries)
            index += 1

        # Formatting the entries for the dictionary.
        dictionary = u""
        for dictionaryEntry in self.formatEntriesForDictionary(parsedEntries, self.partOfSpeech):
            dictionary += dictionaryEntry

        return dictionary


# Entry generator.

class EntryGenerator(object):

    def __init__(self, site=None, pageGenerators=[], pageParser=None, entryParser=None):

        self.site = site
        self.pageGenerators = pageGenerators

        if not pageParser:
            pageParser = TitleParser()
        self.pageParser = pageParser

        if not entryParser:
            entryParser = EntryParser()
        self.entryParser = entryParser


    def setSite(self, site):
        self.site = site
        for pageGenerator in self.pageGenerators:
            pageGenerator.setSite(self.site)




# Page generators.

class PageGenerator(object):
    def run(self):
        raise Exception("Abstract method")


class CategoryBrowser(PageGenerator):

    def __init__(self, site=None,
                 categoryNames=[], ignoreCategoryNames=[], categoryOfCategoriesNames=[],
                 invalidPagePattern=None, validCategoryPattern=None, invalidCategoryPattern=None):

        # Site.
        self.site = site

        # Lists.
        self.categoryNames = categoryNames
        self.ignoreCategoryNames = ignoreCategoryNames
        self.categoryOfCategoriesNames = categoryOfCategoriesNames

        # Patterns.
        self.invalidPagePattern = parsePattern(invalidPagePattern)
        self.validCategoryPattern = parsePattern(validCategoryPattern)
        self.invalidCategoryPattern = parsePattern(invalidCategoryPattern)

        # Internal.
        self.visitedCategoryNames = set()
        self.pagesNamesToIgnore = set()


    def setSite(self, site):
        self.site = site


    def pageTitleMatchesPattern(self, page, pattern):
        return pattern is not None and pattern.match(page.title(withNamespace=False))


    def pageIsValid(self, page):
        if self.pageTitleMatchesPattern(page, self.invalidPagePattern):
            return False
        if page.title(withNamespace=False) in self.pagesNamesToIgnore:
            return False
        return True


    def canLoadPagesFromCategory(self, category):
        return self.pageTitleMatchesPattern(category, self.validCategoryPattern)


    def canTreatCategoryAsPage(self, category):
        return not self.pageTitleMatchesPattern(category, self.invalidCategoryPattern)


    def loadPagesFromCategory(self, category, reporter):
        self.visitedCategoryNames.add(category.title(withNamespace=False))
        for page in category.articles(namespaces=0):
            if self.pageIsValid(page):
                yield page
        reporter.done()
        for subcategory in category.subcategories():
            subcategoryName = subcategory.title(withNamespace=False)
            if subcategoryName not in self.visitedCategoryNames:
                if self.canLoadPagesFromCategory(subcategory):
                    subcategoryReporter = TaskInProgressReporter(u"Cargando o contido da categoría «{}»".format(subcategoryName), indent=reporter.indent+2)
                    for page in self.loadPagesFromCategory(subcategory, subcategoryReporter):
                        yield page
                elif self.canTreatCategoryAsPage(subcategory):
                    if self.pageIsValid(subcategory):
                        yield subcategory


    def loadPagesFromCategoryIntoIgnoreList(self, category):
        self.visitedCategoryNames.add(category.title(withNamespace=False))
        for page in category.articles(namespaces=0):
            self.pagesNamesToIgnore.add(page.title())


    def run(self):

        if self.ignoreCategoryNames:
            output(u"• Obtendo unha lista de páxinas a ignorar…\n")
            for categoryName in self.ignoreCategoryNames:
                if categoryName not in self.visitedCategoryNames:
                    reporter = TaskInProgressReporter(u"Cargando o contido da categoría «{}»".format(categoryName), indent=2)
                    self.loadPagesFromCategoryIntoIgnoreList(pywikibot.Category(self.site, categoryName))
                    reporter.done()

        if self.categoryNames:
            output(u"• Obtendo páxinas da lista de categorías…\n")
            for categoryName in self.categoryNames:
                if categoryName not in self.visitedCategoryNames:
                    reporter = TaskInProgressReporter(u"Cargando o contido da categoría «{}»".format(categoryName), indent=2)
                    for page in self.loadPagesFromCategory(pywikibot.Category(self.site, categoryName), reporter):
                        yield page

        if self.categoryOfCategoriesNames:
            output(u"• Obtendo páxinas da lista de categorías de categorías…\n")
            for categoryName in self.categoryOfCategoriesNames:
                for subcategory in pywikibot.Category(self.site, categoryName).subcategories():
                    subcategoryName = subcategory.title(withNamespace=False)
                    if subcategoryName not in self.visitedCategoryNames:
                        reporter = TaskInProgressReporter(u"Cargando o contido da categoría «{}»".format(subcategoryName), indent=2)
                        for page in self.loadPagesFromCategory(subcategory, reporter):
                            yield page


class PageLoader(PageGenerator):

    def __init__(self, site=None, pageNames=[]):
        self.site = site
        self.pageNames = pageNames


    def setSite(self, site):
        self.site = site


    def run(self):
        reporter = ProgressReporter(u"Cargando a lista de páxinas", len(self.pageNames))
        for pageName in self.pageNames:
            yield pywikibot.Page(self.site, pageName)
            reporter.increase()
        reporter.done()




# Page parsers.

class PageParser(object):
    def parse(self, pages):
        raise Exception("Abstract method")



class TitleParser(PageParser):

    def parse(self, pages, statement=u"Obtendo o título das páxinas"):
        reporter = ProgressReporter(statement, len(pages))
        for page in pages:
            yield page.title(withNamespace=False)
            reporter.increase()
        reporter.done()



class SiteCache(object):

    def __init__(self, site):

        self.site = site
        cacheManager = CacheManager()

        self.cacheFolder = os.path.join(cacheManager.cacheFolder, "mediawiki", u"{}-{}".format(site.family.name, site.lang))
        if not os.path.exists(self.cacheFolder):
            os.makedirs(self.cacheFolder)

        self.cacheTestsFolder = os.path.join(cacheManager.cacheFolder, "mediawiki", u"tests")
        if not os.path.exists(self.cacheTestsFolder):
            os.makedirs(self.cacheTestsFolder)

        familyCode = site.family.name
        if familyCode == u"wikipedia":
            familyCode = u"wiki"
        self._siteCode = site.lang + familyCode

        self.dumpFileNameTemplate = self.siteCode() + u"-{}-pages-articles.xml.bz2"
        self.pageDumpPattern = re.compile(self.dumpFileNameTemplate.format(u"(?P<date>[0-9]{8})"))

        self._dumpUrl = None
        self._dumpDownloadBytesPerSecond = None
        self._dumpParsingBytesPerSecond = None
        self._dumpDownloadBytes = None
        self._remoteDumpDate = None
        self._localDumpDate = None
        self._localDumpPath = None
        self._needToDownloadDump = None


    def pageNamesToLoadFromWikiFilePath(self):
        return os.path.join(self.cacheFolder, u"pageNamesToLoadFromWiki.json")


    def pageNamesToLoadFromWiki(self):
        filePath = self.pageNamesToLoadFromWikiFilePath()
        if os.path.exists(filePath):
            with codecs.open(filePath, "r", "utf-8") as fileObject:
                return json.load(fileObject)
        return []


    def siteCode(self):
        return self._siteCode


    def remoteDumpDate(self):
        if not self._remoteDumpDate:
            request = urllib2.Request(u"http://dumps.wikimedia.org/{}wiki/".format(self.site.lang))
            response = urllib2.urlopen(request)
            page = response.read()
            soup = BeautifulSoup(page)
            self._remoteDumpDate = int(soup.find_all("tr")[-2].td.a.get_text())
        return self._remoteDumpDate


    def dumpUrl(self):
        if not self._dumpUrl:
            self._dumpUrl = u"http://dumps.wikimedia.org/{}/{}/{}".format(
                self.siteCode(),
                self.remoteDumpDate(),
                self.dumpFileNameTemplate.format(self.remoteDumpDate()),
            )
        return self._dumpUrl


    def dumpDownloadBytes(self):
        if not self._dumpDownloadBytes:
            response = requests.head(self.dumpUrl())
            self._dumpDownloadBytes = response.headers.get('content-length')
        return self._dumpDownloadBytes


    def dumpDownloadBytesPerSecond(self):
        if not self._dumpDownloadBytesPerSecond:
            testFileUrl = u"http://dumps.wikimedia.org/ttwiki/latest/ttwiki-latest-abstract.xml-rss.xml"
            response = requests.get(testFileUrl, stream=True)
            byteCount = float(response.headers.get('content-length'))
            seconds = response.elapsed.total_seconds()
            self._dumpDownloadBytesPerSecond = byteCount/seconds
        return self._dumpDownloadBytesPerSecond


    def dumpParsingBytesPerSecond(self):

        if not self._dumpParsingBytesPerSecond:

            localFileName = u"articles.xml.bz2"
            localFilePath = os.path.join(self.cacheTestsFolder, localFileName)
            if not os.path.exists(localFilePath):
                testFileUrl = u"http://dumps.wikimedia.org/ttwikiquote/latest/ttwikiquote-latest-pages-articles.xml.bz2"
                urllib.urlretrieve(testFileUrl, localFilePath)

            byteCount = float(os.path.getsize(localFilePath))

            start = time.clock()
            xmlReader = XmlDump(localFilePath)
            xmlReader.parse()
            seconds = time.clock() - start

            self._dumpParsingBytesPerSecond = byteCount/seconds

        return self._dumpParsingBytesPerSecond


    def dumpDownloadBytes(self):
        if not self._dumpDownloadBytes:
            response = requests.head(self.dumpUrl())
            self._dumpDownloadBytes = float(response.headers.get('content-length'))
        return self._dumpDownloadBytes


    def localDumpDate(self):
        if not self._localDumpDate:
            for filePath in [filePath for filePath in os.listdir(self.cacheFolder) if os.path.isfile(os.path.join(self.cacheFolder, filePath))]:
                match = self.pageDumpPattern.match(filePath)
                if match:
                    self._localDumpDate = int(match.group(u"date"))
                    break
        return self._localDumpDate


    def localDumpPath(self):
        if self._localDumpPath is None:
            localDumpDate = self.localDumpDate()
            if localDumpDate:
                localDumpFileName = self.dumpFileNameTemplate.format(localDumpDate)
                self._localDumpPath = os.path.join(self.cacheFolder, localDumpFileName)
            else:
                self._localDumpPath = False # No local dump.
        return self._localDumpPath


    def needToDownloadDump(self):
        if self._needToDownloadDump is None:
            localDumpDate = self.localDumpDate()
            self._needToDownloadDump = not localDumpDate or localDumpDate < self.remoteDumpDate()
        return self._needToDownloadDump


    def downloadDumpIfNeeded(self):

        if self.needToDownloadDump():

            localDumpPath = self.localDumpPath()
            if localDumpPath:
                os.remove(localDumpPath)

            filePath = self.pageNamesToLoadFromWikiFilePath()
            if os.path.exists(filePath):
                with open(filePath, "w") as fileObject:
                    fileObject.write("")

            self._localDumpDate = self.remoteDumpDate()
            dumpFileName = self.dumpFileNameTemplate.format(self._localDumpDate)
            self._localDumpPath = os.path.join(self.cacheFolder, dumpFileName)
            urllib.urlretrieve(self.dumpUrl(), self._localDumpPath)

            self._needToDownloadDump = False



class PageContentLoader(object):
    """Helper class for those page parsers that require to load the content of
    the pages.

    This class determines whether or not it is worth it to use a MediaWiki dump
    instead of loading the pages using the API.

    If it is worth it, the class loads all pages that it can from a dump. Pages
    not found in the dump or marked as requiring the latest version from the
    MediaWiki server are then obtained using the API.
    """

    mainArticleTemplatePatterns = {
        "gl": re.compile(u"(?i)\{\{ *(?P<template>AP|Artigo principal) *(\| *(?P<page>[^|}]+) *)?(\|[^|}]*)*\}\}"),
        "es": re.compile(u"(?i)\{\{ *(?P<template>AP) *(\| *(?P<page>[^|}]+) *)?(\|[^|}]*)*\}\}"),
    }


    def mainCategoryArticle(category):

        mainArticleName = None

        languageCode = category.site.lang
        if languageCode in mainArticleTemplatePatterns:

            content = category.get()

            match = mainArticleTemplatePatterns[languageCode].search(content)
            if match.group("page"):
                mainArticleName = match.group("page")
            elif match.group("template"):
                mainArticleName = category.title(withNamespace=False)

            if mainArticleName:
                page = pywikibot.Page(category.site, mainArticleName)
                if page.exists():
                    return page

        return None


    def __init__(self, pages, forceWiki=False):

        if pages:

            for page in pages:
                self.site = page.site
                self.siteCache = SiteCache(self.site)
                break

            pageNamesToLoadFromWiki = self.siteCache.pageNamesToLoadFromWiki()

        self.forceWiki = forceWiki

        self.pagesToLoadFromXmlDump = {}
        self.pagesToLoadFromWiki = set()
        self._pagesWithoutContent = set()

        for page in pages:
            if page.isCategory():
                mainArticle = mainCategoryArticle(page)
                if mainArticle:
                    self.pagesToLoadFromXmlDump[mainArticle.title(withNamespace=False)] = mainArticle
                else:
                    self._pagesWithoutContent.add(page)
            else:
                pageName = page.title(withNamespace=False)
                if pageName in pageNamesToLoadFromWiki:
                    self.pagesToLoadFromWiki.add(pywikibot.Page(self.site, pageName))
                else:
                    self.pagesToLoadFromXmlDump[pageName] = page

        self._xmlReader = None
        self._calculateSecondsToLoadOnePageFromWiki = None
        self._usingXmlDumpIsQuicker = None


    def pagesWithoutContent(self):
        return self._pagesWithoutContent


    def secondsToLoadOnePageFromWiki(self):
        if not self._calculateSecondsToLoadOnePageFromWiki:
            start = time.clock()
            for pageName, page in self.pagesToLoadFromXmlDump.iteritems():
                page.get()
                break
            self._calculateSecondsToLoadOnePageFromWiki = time.clock() - start
        return self._calculateSecondsToLoadOnePageFromWiki


    def usingXmlDump(self):

        if self.forceWiki:
            return False

        if self._usingXmlDumpIsQuicker is None:

            secondsToLoadOnePageFromWiki = self.secondsToLoadOnePageFromWiki()
            pagesCount = len(self.pagesToLoadFromXmlDump)
            secondsToLoadRequiredPagesFromWiki = pagesCount * secondsToLoadOnePageFromWiki

            secondsToDownloadDump = 0
            if self.siteCache.needToDownloadDump():
                dumpBytes = self.siteCache.dumpDownloadBytes()
                bytesPerSecond = self.siteCache.dumpDownloadBytesPerSecond()
                secondsToDownloadDump = dumpBytes / bytesPerSecond
                if secondsToDownloadDump > secondsToLoadRequiredPagesFromWiki:
                    self._usingXmlDumpIsQuicker = False
                    return self._usingXmlDumpIsQuicker
            else:
                dumpBytes = self.siteCache.dumpBytes()

            bytesPerSecond = self.siteCache.dumpParsingBytesPerSecond()
            secondsToParseDump = dumpBytes / bytesPerSecond
            secondsToUseDump = secondsToDownloadDump + secondsToParseDump
            self._usingXmlDumpIsQuicker = secondsToUseDump < secondsToLoadRequiredPagesFromWiki

        return self._usingXmlDumpIsQuicker


    def xmlReader(self):
        if not self._xmlReader:
            self.siteCache.downloadDumpIfNeeded()
            self._xmlReader = XmlDump(self.siteCache.localDumpPath())
        return self._xmlReader


    def run(self):

        if self.usingXmlDump():
            for entry in self.xmlReader().parse():
                if entry.title in self.pagesToLoadFromXmlDump:
                    yield self.pagesToLoadFromXmlDump[entry.title], entry.text, "cache"
                    del self.pagesToLoadFromXmlDump[entry.title]

        for pageName, page in self.pagesToLoadFromXmlDump.iteritems():
            yield page, page.get(), "wiki"
        for page in self.pagesToLoadFromWiki:
            yield page, page.get(), "wiki"



class PageContentParser(PageParser):

    def __init__(self):
        self.pagesWithWrongContentInCache = set()
        self.pagesWithWrongContentOnline = set()
        self.pagesWithoutContent = set()


    def parsePageContent(self, page, content, source):
        raise Exception("Abstract method")


    def parse(self, pages):

        reporter = ProgressReporter(u"Analizando o contido das páxinas", len(pages))
        pageContentLoader = PageContentLoader(pages)
        for page, content, source in pageContentLoader.run():
            for entry in self.parsePageContent(page, content, source):
                yield entry
            reporter.increase()
        reporter.done()
        self.pagesWithoutContent = self.pagesWithoutContent.union(pageContentLoader.pagesWithoutContent())

        reporter = ProgressReporter(u"Analizando a última versión das páxinas con contido problemático na caché", len(self.pagesWithWrongContentInCache))
        pageContentLoader = PageContentLoader(self.pagesWithWrongContentInCache, forceWiki=True)
        for page, content, source in pageContentLoader.run():
            for entry in self.parsePageContent(page, content, source):
                yield entry
            reporter.increase()
        reporter.done()

        pageNamesWithWrongContentOnline = set()
        for entry in TitleParser().parse(self.pagesWithWrongContentOnline, u"Obtendo o nome das páxinas con contido problemático na súa última versión"):
            yield entry
            pageNamesWithWrongContentOnline.add(entry)
        for pageName in pageNamesWithWrongContentOnline:
            output(u"  • {}\n".format(pageName))

        pageNamesWithoutContent = set()
        for entry in TitleParser().parse(self.pagesWithoutContent, u"Obtendo o nome das páxinas sen contido"):
            yield entry
            pageNamesWithoutContent.add(entry)
        for pageName in pageNamesWithoutContent:
            output(u"  • {}\n".format(pageName))



class LineParser(PageContentParser):

    def __init__(self, linePattern, ignorePattern=None):
        super(LineParser, self).__init__()
        self.linePattern = parsePattern(linePattern)
        self.ignorePattern = parsePattern(ignorePattern)

    def isRtl(self, text):
        # http://stackoverflow.com/a/17685399/939364
        return len([None for character in text if unicodedata.bidirectional(character) in ('R', 'AL')])/float(len(text)) > 0.1


    def entryIsValid(self, entry):
        if self.ignorePattern and self.ignorePattern.match(entry):
            return False
        if self.isRtl(entry):
            return False
        return True


    def parsePageContent(self, page, content, source):
        for line in content.splitlines():
            match = self.linePattern.match(line)
            if match:
                entry = match.group(u"entry")
                if self.entryIsValid(entry):
                    yield entry



class FirstSentenceParser(PageContentParser):

    def __init__(self):
        super(FirstSentenceParser, self).__init__()


    def removeMediaWikiFileTags(self, content):
        return fileTagPattern.sub(u"", content)


    def registerPageWithWrongContent(self, page, source):
        if source == "cache":
            self.pagesWithWrongContentInCache.add(page)
        elif source == "wiki":
            self.pagesWithWrongContentOnline.add(page)
        else:
            raise ValueError(u"Unexpected source: '{}'".format(source))


    def getFirstSentence(self, page, content, source):

        if page.isRedirectPage():
            if source == "cache":
                self.pagesWithWrongContentInCache.add(page)
            elif source == "wiki":
                self.pagesWithoutContent.add(page)
            else:
                raise ValueError(u"Unexpected source: '{}'".format(source))
            return None

        templateDepth = 0
        tableDepth = 0
        fileDepth = 0
        htmlStartTags = []

        for line in content.split('\n'):
            line = self.removeMediaWikiFileTags(line).rstrip()
            if line:

                tableDepth += sum(1 for match in tableStartTagPattern.finditer(line))
                lineTableEndTagsCount = sum(1 for match in tableEndTagPattern.finditer(line))
                tableDepth -= lineTableEndTagsCount
                if lineTableEndTagsCount and line.startswith("|}"):
                    line = line[2:]
                    if not line:
                        continue

                if line[0] not in [' ', '{', '}', '|', '[', ':', '!', '<'] and not templateDepth and not tableDepth and not fileDepth and not htmlStartTags:
                    line = re.sub(parenthesis, u"", line) # Eliminar contido entre parénteses.
                    line = re.sub(reference, u"", line) # Eliminar contido de referencia.
                    return sentenceSeparatorPattern.split(line)[0]

                templateDepth += line.count("{{")
                templateDepth -= line.count("}}")

                lineFileDepth = sum(1 for match in fileStartTagPattern.finditer(line))
                fileDepth += lineFileDepth
                fileDepth -= line.count(u"]]") - line.count(u"[[") + lineFileDepth

                for startTag in htmlStartTagPattern.findall(line):
                    if startTag not in tagsToSkip:
                        htmlStartTags.append(startTag)
                for endTag in htmlEndTagPattern.findall(line):
                    if endTag in tagsToSkip:
                        pass
                    elif endTag in htmlStartTags:
                        htmlStartTags.remove(endTag)
                    else:
                        return None

        return None


    def parsePageContent(self, page, content, source):

        firstSentence = self.getFirstSentence(page, content, source)
        if firstSentence is None:
            self.registerPageWithWrongContent(page, source)
            return

        matches = boldPattern.findall(firstSentence)
        if len(matches) == 0:
            self.registerPageWithWrongContent(page, source)
            return

        for match in matches:
            match = wikiTags.sub(u"", match) # Eliminar etiquetas MediaWiki, como [[ ou ]].
            yield match


# Entry parser.

class EntryParser(object):

    def __init__(self,
                 basqueFilter=False,
                 commaFilter=True,
                 hyphenFilter=True):
        self.basqueFilter = basqueFilter
        self.commaFilter = commaFilter
        self.hyphenFilter = hyphenFilter


    def applyMandatoryFilters(self, entry):
        entry = re.sub(parenthesis, u"", entry) # Eliminar contido entre parénteses.
        entry = entry.strip()
        entry = entry.strip(u'\ufeff') # http://stackoverflow.com/a/6786646
        return entry


    def parse(self, entries):
        for entry in entries:
            if self.commaFilter and "," in entry: # Datos adicionais para localizar o lugar. Por exemplo: «Durango, País Vasco».
                entry = entry.split(",")[0]
            if self.hyphenFilter and " - " in entry: # Nome en galego e no idioma local. Por exemplo: «Bilbao - Bilbo».
                entry = entry.split(" - ")[0]
            if self.basqueFilter and "-" in entry: # Nome éuscara oficial, en éuscara e castelán. Por exemplo: «Valle de Trápaga-Trapagaran».
                entry = entry.split("-")
            if isinstance(entry, basestring):
                yield self.applyMandatoryFilters(entry)
            else:
                for subentry in entry:
                    yield self.applyMandatoryFilters(subentry)