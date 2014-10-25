# -*- coding:utf-8 -*-

import codecs, json, os, requests, sys, tempfile, time, unicodedata, urllib
import urllib2
import regex as re

from bs4 import BeautifulSoup

import pywikibot
from pywikibot.xmlreader import XmlDump

from common import CacheManager, ProgressReporter, TaskInProgressReporter, formatEntriesForDictionary
from generator import Generator, output, wordsToIgnore



fileTagPattern = re.compile(u"(?i)\[\[ *(File|Image|Ficheiro|Imaxe):([^][]|\[\[[^][]+\]\])+\]\] *")
htmlStartTagPattern = re.compile(u"< *(\w+)[^>]*?(?<!/)>")
htmlEndTagPattern = re.compile(u"</ *(\w+) *>")
tagsToSkip = [u"br", "hr"]
tableStartTagPattern = re.compile(u"(?<!\{)\{\|")
tableEndTagPattern = re.compile(u"\|\}(?!\})")
fileStartTagPattern = re.compile(u"(?i)\[\[ *(File|Image|Ficheiro|Imaxe):")


sep = u"(?:[-,;]| e ) *"
colon = u"(?:[:,] *)?"
nexo = u"(?:do|en) *"

term = u"(?:\'\'\'\'\' *[^)]*? *\'\'\'\'\'|\'\'\' *[^)]*? *\'\'\'|\'\' *[^)]*? *\'\'|\{\{ *nihongo *\|.*?\}\}) *"
thisOrThat = u"(?:abreviado *)?{term}(?: *ou *{term})? *".format(term=term)
language = u"(?:\w+|\[\[[^]|]+\|[^]]+\]\]) *"

termo = u"(?:\'\'\'\'\' *([^)]*?) *\'\'\'\'\'|\'\'\' *([^)]*?) *\'\'\'|\'\' *([^)]*?) *\'\'|\{\{ *nihongo *\| *(.*?) *\|.*?\}\}) *"
istoOuAquilo = u"(?:abreviado *)?{term}(?: *ou *{term})? *".format(term=termo)
galego = u"(?:galego|\[\[[^]|]+\| *galego *\]\]) *"

friends = u"(?:(?:(?:{frase1}|{frase2})(?:{sep}{istoOuAquilo})?)|(?:(?:{phrase1}|{phrase2}|{phrase4})(?:{sep}{thisOrThat})?))" \
         u"(?:{sep}(?:(?:(?:{frase1}|{frase2}|{frase3})(?:{sep}{istoOuAquilo})?)|(?:(?:{phrase1}|{phrase2}|{phrase3}|{phrase4})(?:{sep}{thisOrThat})?)))*".format(
    frase1=nexo+galego+colon+istoOuAquilo,
    frase2=istoOuAquilo+nexo+galego,
    frase3=galego+colon+istoOuAquilo,
    phrase1=nexo+language+colon+thisOrThat,
    phrase2=thisOrThat+nexo+language,
    phrase3=language+colon+thisOrThat,
    phrase4=u"\{{\{{ *lang-[^|]+\|{}\}}\}}".format(term),
    sep=sep,
    istoOuAquilo=istoOuAquilo,
    thisOrThat=thisOrThat,
)

siglasWasp = u"\'\'\'\w\'\'\'\'\'\w*\'\'(?:[\w, -]+\'\'\'\w\'\'\'\'\'\w*\'\')*"  # e.g. https://gl.wikipedia.org/wiki/WASP
siglasAbap = u"\'\'\'\'\'\w\'\'\'\w*(?:[\w, -]+\'\'\'\w\'\'\'\w*)*\'\'"  # e.g. https://gl.wikipedia.org/wiki/ABAP
siglasPl1 = u"\'\'\'\w\'\'\'\w*(?:[\w, -]+\'\'\'\w\'\'\'\w*)*"  # e.g. https://gl.wikipedia.org/wiki/PL/1

highlightedPatternStrings = [
    u"\( *\'\'\' *\[[^ ]+\.ogg +\'\' *[^)]+ *\'\' *\] *\'\'\' *\)",
    u"\( *{term}, *(?:.*?, *)*literalmente *{term} *\)".format(term=term),  # e.g. https://gl.wikipedia.org/wiki/O_Correcami%C3%B1os
    u"\( *{thisOrThat}{sep}{friends}(?:{sep}{friends})* *\)".format(thisOrThat=istoOuAquilo, sep=sep, friends=friends),
    u"\( *{}\)".format(friends),
    u"\( *{term}{sep}na *actualidade *{term}\)".format(term=termo, sep=sep),
    u"\( *{term},? *ou *{term}\)".format(term=termo),
    u"\( *{term}{sep}{term}\)".format(term=termo, sep=sep),
    u"\( *(?:{}) *\)".format(u"|".join((siglasWasp, siglasAbap, siglasPl1))),
    u"\( *{}\)".format(termo),
    u"|".join((siglasWasp, siglasAbap, siglasPl1)),
    u"\'\'\'\'\' *(.*?) *\'\'\'\'\'",
    u"\'\'\' *\{\{ *nihongo *\| *(.*?) *\|.*?\}\} *\'\'\'",
    u"\'\'\' *(.*?) *\'\'\'",
]
highlightedPatterns = [re.compile(patternString, re.UNICODE) for patternString in highlightedPatternStrings]


parenthesis = re.compile(u" *\([^)]*\)")
reference = re.compile(u"< *ref[^>]*>.*?< */ *ref *>")
sentenceSeparatorPattern = re.compile(u"(?<!(a\.C|..D|d\.C|.St|..[A-Z]))\. ")



# Helpers.

_regexType = type(re.compile(u"."))

def parsePattern(pattern):
    if not pattern:
        return pattern
    if not isinstance(pattern, _regexType):
        pattern = re.compile(pattern)
    return pattern



# Dictionary generators.

class MediaWikiGenerator(Generator):


    def __init__(self, siteName, languageCode, resource, partOfSpeech, entryGenerators):

        self.resource = u"{}/{}/{}".format(siteName, languageCode, resource)
        self.partOfSpeech = partOfSpeech

        site = pywikibot.Site(languageCode, siteName)
        for entryGenerator in entryGenerators:
            entryGenerator.setSite(site)
        self.entryGenerators = entryGenerators


    def evaluateNoCacheParameters(self):
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
        #
        # Optionally, an index can be specified to skip cache only on one
        # entryGenerator. For example:
        #
        #     -nocache:2
        #     -nocache:pageParser:1
        #
        noCache = {}
        for arg in sys.argv:
            arg = arg.decode("utf-8")
            if arg.startswith(u"-nocache"):
                pieces = arg.split(u":")
                piecesCount = len(pieces)

                if piecesCount == 1:
                    noCache["pageGenerators"] = True
                    noCache["pageParser"] = True
                    noCache["entryParser"] = True

                elif piecesCount == 2:

                    if pieces[1].isdigit():

                        if "pageGenerators" in noCache and noCache["pageGenerators"] != True:
                            noCache["pageGenerators"].append(int(pieces[1]))
                        else:
                            noCache["pageGenerators"] = [int(pieces[1]),]

                        if "pageParser" in noCache and noCache["pageParser"] != True:
                            noCache["pageParser"].append(int(pieces[1]))
                        else:
                            noCache["pageParser"] = [int(pieces[1]),]

                        if "entryParser" in noCache and noCache["entryParser"] != True:
                            noCache["entryParser"].append(int(pieces[1]))
                        else:
                            noCache["entryParser"] = [int(pieces[1]),]

                    elif pieces[1] == u"pageGenerators":

                        noCache["pageGenerators"] = True
                        noCache["pageParser"] = True
                        noCache["entryParser"] = True

                    elif pieces[1] == u"pageParser":

                        noCache["pageParser"] = True
                        noCache["entryParser"] = True

                    elif pieces[1] == u"entryParser":

                        noCache["entryParser"] = True

                elif piecesCount == 3:

                    if pieces[1] == u"pageGenerators":

                        if "pageGenerators" in noCache and noCache["pageGenerators"] != True:
                            noCache["pageGenerators"].append(int(pieces[2]))
                        else:
                            noCache["pageGenerators"] = [int(pieces[2]),]

                        if "pageParser" in noCache and noCache["pageParser"] != True:
                            noCache["pageParser"].append(int(pieces[2]))
                        else:
                            noCache["pageParser"] = [int(pieces[2]),]

                        if "entryParser" in noCache and noCache["entryParser"] != True:
                            noCache["entryParser"].append(int(pieces[2]))
                        else:
                            noCache["entryParser"] = [int(pieces[2]),]

                    elif pieces[1] == u"pageParser":

                        if "pageParser" in noCache and noCache["pageParser"] != True:
                            noCache["pageParser"].append(int(pieces[2]))
                        else:
                            noCache["pageParser"] = [int(pieces[2]),]

                        if "entryParser" in noCache and noCache["entryParser"] != True:
                            noCache["entryParser"].append(int(pieces[2]))
                        else:
                            noCache["entryParser"] = [int(pieces[2]),]

                    elif pieces[1] == u"entryParser":

                        if "entryParser" in noCache and noCache["entryParser"] != True:
                            noCache["entryParser"].append(int(pieces[2]))
                        else:
                            noCache["entryParser"] = [int(pieces[2]),]

        return noCache


    def generateFileContent(self):

        noCache = self.evaluateNoCacheParameters()
        cacheManager = CacheManager()
        totalEntries = set()
        index = 1

        for entryGenerator in self.entryGenerators:

            # Obtaining a list of pages to parse.
            cacheName = u"pageNames" + unicode(index)
            if cacheManager.exists(self.resource, cacheName) and ("pageGenerators" not in noCache or (noCache["pageGenerators"] is not True and index not in noCache["pageGenerators"])):
                pages = [pywikibot.Page(entryGenerator.site, pageName) for pageName in cacheManager.load(self.resource, cacheName)]
            else:
                pages = set()
                for pageGenerator in entryGenerator.pageGenerators:
                    for page in pageGenerator.run():
                        pages.add(page)
                cacheManager.save(self.resource, cacheName, [page.title() for page in pages])

            # Parsing the pages to obtain a list of entries.
            cacheName = u"entries" + unicode(index)
            if cacheManager.exists(self.resource, cacheName) and ("pageParser" not in noCache or (noCache["pageParser"] is not True and index not in noCache["pageParser"])):
                entries = cacheManager.load(self.resource, cacheName)
            else:
                entries = set()
                for entry in entryGenerator.pageParser.parse(pages):
                    entries.add(entry)
                cacheManager.save(self.resource, cacheName, entries)

            # Parsing the entries.
            cacheName = u"parsedEntries" + unicode(index)
            if cacheManager.exists(self.resource, cacheName) and ("entryParser" not in noCache or (noCache["entryParser"] is not True and index not in noCache["entryParser"])):
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
        for dictionaryEntry in formatEntriesForDictionary(totalEntries, self.partOfSpeech):
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
                 categoryOfPagesNames=[],
                 validPagePattern=None, invalidPagePattern=None,
                 validCategoryPattern=None, invalidCategoryPattern=None,
                 invalidCategoryAsPagePattern=None):

        # Site.
        self.site = site

        # Lists.
        self.categoryNames = categoryNames
        self.ignoreCategoryNames = ignoreCategoryNames
        self.categoryOfCategoriesNames = categoryOfCategoriesNames
        self.categoryOfPagesNames = categoryOfPagesNames

        # Patterns.
        self.validPagePattern = parsePattern(validPagePattern)
        self.invalidPagePattern = parsePattern(invalidPagePattern)
        self.validCategoryPattern = parsePattern(validCategoryPattern)
        self.invalidCategoryPattern = parsePattern(invalidCategoryPattern)
        self.invalidCategoryAsPagePattern = parsePattern(invalidCategoryAsPagePattern)

        # Internal.
        self.visitedCategoryNames = set()
        self.pagesNamesToIgnore = set()


    def setSite(self, site):
        self.site = site


    def pageTitleMatchesPattern(self, page, pattern):
        return pattern is not None and pattern.match(page.title(withNamespace=False))


    def pageIsValid(self, page):
        if page.title(withNamespace=False) in self.pagesNamesToIgnore:
            return False
        if self.validPagePattern is not None:
            return self.validPagePattern.match(page.title(withNamespace=False))
        if self.pageTitleMatchesPattern(page, self.invalidPagePattern):
            return False
        return True


    def canLoadPagesFromCategory(self, category):
        if self.validCategoryPattern is not None:
            return self.validCategoryPattern.match(category.title(withNamespace=False))
        if self.pageTitleMatchesPattern(category, self.invalidCategoryPattern):
            return False
        return True


    def canTreatCategoryAsPage(self, category):
        return not self.pageTitleMatchesPattern(category, self.invalidCategoryAsPagePattern)


    def loadPagesFromCategory(self, category, reporter):
        category_name = category.title(withNamespace=False)
        self.visitedCategoryNames.add(category_name)
        for page in category.articles(namespaces=0):
            if self.pageIsValid(page):
                yield page
        reporter.done()
        for subcategory in category.subcategories():
            subcategoryName = subcategory.title(withNamespace=False)
            if subcategoryName not in self.visitedCategoryNames and \
               subcategoryName not in self.categoryNames and \
               subcategoryName not in self.categoryOfCategoriesNames and \
               subcategoryName not in self.categoryOfPagesNames:
                if not self.categoryOfPagesNames and self.canLoadPagesFromCategory(subcategory):
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

        if self.categoryOfPagesNames:
            output(u"• Obtendo páxinas da lista de categorías de páxinas…\n")
            for categoryName in self.categoryOfPagesNames:
                reporter = TaskInProgressReporter(u"Cargando o contido da categoría «{}»".format(categoryName), indent=2)
                category = pywikibot.Category(self.site, categoryName)
                for page in self.loadPagesFromCategory(category, reporter):
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



class MediawikiDumpServerForbidsAccessException(Exception):
    pass


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
        self._dumpBytes = None
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
            try:
                with codecs.open(filePath, "r", "utf-8") as fileObject:
                    return json.load(fileObject)
            except:
                pass
        else:
            with open(filePath, "w") as fileObject:
                fileObject.write("")
        return []


    def siteCode(self):
        return self._siteCode


    def remoteDumpDate(self):
        if not self._remoteDumpDate:
            opener = urllib2.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:29.0) Gecko/20100101 Firefox/29.0')]
            try:
                response = opener.open(u"http://dumps.wikimedia.org/{}/".format(self.siteCode()))
                page = response.read()
                soup = BeautifulSoup(page)
                self._remoteDumpDate = int(soup.find_all("tr")[-2].td.a.get_text())
            except urllib2.HTTPError:
                # Most likely “HTTP Error 403: Forbidden”
                raise MediawikiDumpServerForbidsAccessException()
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
            self._dumpDownloadBytes = float(response.headers.get('content-length'))
        return self._dumpDownloadBytes


    def dumpDownloadBytesPerSecond(self):
        if not self._dumpDownloadBytesPerSecond:
            testFileUrl = u"http://dumps.wikimedia.org/astwiki/latest/astwiki-latest-pages-logging.xml.gz" # ~1.5 MB
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
            for entry in xmlReader.parse():
                pass
            seconds = time.clock() - start

            self._dumpParsingBytesPerSecond = byteCount/seconds

        return self._dumpParsingBytesPerSecond


    def dumpBytes(self):
        if not self._dumpBytes:
            self._dumpBytes = float(os.path.getsize(self.localDumpPath()))
        return self._dumpBytes


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
            with open(filePath, "w") as fileObject:
                fileObject.write("")

            self._localDumpDate = self.remoteDumpDate()
            dumpFileName = self.dumpFileNameTemplate.format(self._localDumpDate)
            self._localDumpPath = os.path.join(self.cacheFolder, dumpFileName)
            urllib.urlretrieve(self.dumpUrl(), self._localDumpPath)

            self._needToDownloadDump = False



mainArticleTemplatePatterns = {
    "gl": re.compile(u"(?i)\{\{ *(?P<template>AP|Artigo principal) *(\| *(?P<page>[^|}]+) *)?(\|[^|}]*)*\}\}"),
    "es": re.compile(u"(?i)\{\{ *(?P<template>AP) *(\| *(?P<page>[^|}]+) *)?(\|[^|}]*)*\}\}"),
}



class PageContentLoader(object):
    """Helper class for those page parsers that require to load the content of
    the pages.

    This class determines whether or not it is worth it to use a MediaWiki dump
    instead of loading the pages using the API.

    If it is worth it, the class loads all pages that it can from a dump. Pages
    not found in the dump or marked as requiring the latest version from the
    MediaWiki server are then obtained using the API.
    """


    def mainCategoryArticle(self, category):

        mainArticleName = None

        languageCode = category.site.lang
        if languageCode in mainArticleTemplatePatterns:

            content = category.get()

            match = mainArticleTemplatePatterns[languageCode].search(content)
            if match:
                if match.group("page"):
                    mainArticleName = match.group("page")
                elif match.group("template"):
                    mainArticleName = category.title(withNamespace=False)
            else:
                mainArticleName = category.title(withNamespace=False)

            if mainArticleName:
                page = pywikibot.Page(category.site, mainArticleName)
                if page.exists():
                    if page.isRedirectPage():
                       page = page.getRedirectTarget()
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
                mainArticle = self.mainCategoryArticle(page)
                if not mainArticle:
                    self._pagesWithoutContent.add(page)
                    continue
                else:
                    pageName = mainArticle.title(withNamespace=False)
                    page = mainArticle
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
            start = time.time()
            page = pywikibot.Page(self.site, u"Galicia")
            page.get()
            self._calculateSecondsToLoadOnePageFromWiki = time.time() - start
        return self._calculateSecondsToLoadOnePageFromWiki


    def secondsToDisplayString(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return u"%d:%02d:%02d" % (hours, minutes, seconds)


    def bytesAsDisplayString(self, byteCount):
        for x in ['bytes','KB','MB','GB','TB']:
            if byteCount < 1024.0:
                return "%3.1f %s" % (byteCount, x)
            byteCount /= 1024.0


    def usingXmlDump(self):

        if self.forceWiki:
            return False

        if self._usingXmlDumpIsQuicker is None:

            secondsToLoadOnePageFromWiki = self.secondsToLoadOnePageFromWiki()
            pagesCount = len(self.pagesToLoadFromXmlDump)
            secondsToLoadRequiredPagesFromWiki = pagesCount * secondsToLoadOnePageFromWiki
            print
            print u"  • Tempo aproximado que levaría descargar as {} páxinas do wiki dunha nunha: {}".format(pagesCount, self.secondsToDisplayString(secondsToLoadRequiredPagesFromWiki))

            secondsToDownloadDump = 0
            if self.siteCache.needToDownloadDump():
                dumpBytes = self.siteCache.dumpDownloadBytes()
                bytesPerSecond = self.siteCache.dumpDownloadBytesPerSecond()
                secondsToDownloadDump = dumpBytes / bytesPerSecond
                print u"  • Tempo aproximado que levaría descargar unha copia de seguranza do wiki ({}): {}".format(
                    self.bytesAsDisplayString(dumpBytes),
                    self.secondsToDisplayString(secondsToDownloadDump)
                )
                if secondsToDownloadDump > secondsToLoadRequiredPagesFromWiki:
                    print u"  ✓ Descargaranse as páxinas dunha nunha."
                    self._usingXmlDumpIsQuicker = False
                    return self._usingXmlDumpIsQuicker
            else:
                dumpBytes = self.siteCache.dumpBytes()

            bytesPerSecond = self.siteCache.dumpParsingBytesPerSecond()
            secondsToParseDump = dumpBytes / bytesPerSecond
            print u"  • Tempo aproximado que levaría analizar o contido da copia de seguranza do wiki: {}".format(self.secondsToDisplayString(secondsToParseDump))
            secondsToUseDump = secondsToDownloadDump + secondsToParseDump
            self._usingXmlDumpIsQuicker = secondsToUseDump < secondsToLoadRequiredPagesFromWiki
            if self._usingXmlDumpIsQuicker:
                if not secondsToDownloadDump:
                    print u"  ✓ Usarase a copia de seguranza dispoñíbel."
                else:
                    print u"  ✓ Descargarase e usarase unha copia de seguranza."
            else:
                print u"  ✓ Descargaranse as páxinas unha a unha."

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
            content = None
            if not page.isRedirectPage():
                content = page.get()
            else:
                content = page.getRedirectTarget().get()
            yield page, content, "wiki"

        for page in self.pagesToLoadFromWiki:
            content = None
            if not page.isRedirectPage():
                content = page.get()
            else:
                content = page.getRedirectTarget().get()
            yield page, content, "wiki"



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


    def entryIsValid(self, entry):
        if self.ignorePattern and self.ignorePattern.match(entry):
            return False
        return True


    def parsePageContent(self, page, content, source):
        for line in content.splitlines():
            match = self.linePattern.match(line)
            if match:
                entry = match.group(u"entry")
                if self.entryIsValid(entry):
                    yield entry



tablePattern = re.compile(u"(?s)\{\|.*?\|\}")


class TableParser(PageContentParser):

    def __init__(self, cellNumbers, skipRows=[]):
        super(TableParser, self).__init__()
        self.cellNumbers = cellNumbers
        self.skipRows = skipRows


    def iterTables(self, content):
        for match in tablePattern.finditer(content):
            yield match.group()


    def iterRows(self, table):
        tableWithoutTags = "\n".join(table.split("\n")[1:-1])
        for row in tableWithoutTags.split("|-"):
            if u"|" in row: # Senón pode tratarse dun separador ao comezo da táboa.
                yield row


    def parseCell(self, cell):
        if u" |" in cell:
            return "|".join(cell.split(u"|")[1:])
        return cell


    def iterCells(self, row):
        for cell in row.splitlines():
            if cell.startswith("|"): # Skip headers that start with “!”.
                cell = cell[1:]
                if cell and u"||" in cell:
                    for subcell in cell.split(u"||"):
                        yield self.parseCell(subcell)
                else:
                    yield self.parseCell(cell)


    def parsePageContent(self, page, content, source):
        for table in self.iterTables(content):
            rowNumber = 0
            for row in self.iterRows(table):
                if rowNumber not in self.skipRows:
                    cellNumber = 0
                    for cell in self.iterCells(row):
                        if cellNumber in self.cellNumbers and cell:
                            yield cell
                        cellNumber += 1
                rowNumber += 1



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
                    line = re.sub(reference, u"", line) # Eliminar contido de referencia.
                    if line.startswith("D."):
                        line = line[2:]
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

        foundAMatch = False

        for pattern in highlightedPatterns:

            matches = list(pattern.finditer(firstSentence))

            if not foundAMatch and len(matches):
                foundAMatch = True

            for match in matches:
                print pattern.pattern
                print match.groups()
                for entry in match.groups():
                    if entry is not None:
                        yield entry

            firstSentence = pattern.sub(u"", firstSentence)

        if not foundAMatch:
            self.registerPageWithWrongContent(page, source)


# Entry parser.

class EntryParser(object):

    def __init__(self,
                 doubleApostropheFilter=True,
                 basqueFilter=False,
                 colonFilter=True,
                 commaFilter=True,
                 commaSplitter=False,
                 hyphenFilter=True,
                 ignoredEntries=[],
                 linkFilter=True,
                 noRtlFilter=True,
                 quoteFilter=True,
                 semicolonSplitter=False,
                 separatorsSplitter=[],
                 subscriptFilter=True,
                 superscriptFilter=True,
                 unescapeHtml=True,):
        self.doubleApostropheFilter = doubleApostropheFilter
        self.basqueFilter = basqueFilter
        self.colonFilter = colonFilter
        self.commaFilter = commaFilter
        self.commaSplitter = commaSplitter
        self.hyphenFilter = hyphenFilter
        self.ignoredEntries = ignoredEntries
        self.linkFilter = linkFilter
        self.noRtlFilter = noRtlFilter
        self.quoteFilter = quoteFilter
        self.semicolonSplitter = semicolonSplitter
        self.separatorsSplitter = separatorsSplitter
        self.subscriptFilter = subscriptFilter
        self.superscriptFilter = superscriptFilter
        self.unescapeHtml = unescapeHtml

        if self.unescapeHtml:
            import HTMLParser
            self.htmlParser = HTMLParser.HTMLParser()


    def applyMandatoryFilters(self, entry):
        entry = entry.strip()
        entry = entry.strip(u'\ufeff') # http://stackoverflow.com/a/6786646
        entry = entry.lstrip(u'¡')
        entry = entry.rstrip(u'!')
        if entry and entry not in self.ignoredEntries:
            yield entry


    def isRtl(self, text):
        # http://stackoverflow.com/a/17685399/939364
        text = unicode(text)
        return len([None for character in text if unicodedata.bidirectional(character) in ('R', 'AL')])/float(len(text)) > 0.1


    def parse(self, entries):
        for entry in entries:

            # Skippers.
            if not entry:
                continue

            # Modifiers.
            entry = re.sub(parenthesis, u"", entry) # Eliminar contido entre parénteses.
            if self.doubleApostropheFilter and u"''" in entry:
                entry = entry.replace(u"''", u"")
            if self.commaFilter and u"," in entry: # Datos adicionais para localizar o lugar. Por exemplo: «Durango, País Vasco».
                entry = entry.split(u",")[0]
            if self.hyphenFilter and u" - " in entry: # Nome en galego e no idioma local. Por exemplo: «Bilbao - Bilbo».
                entry = entry.split(u" - ")[0]
            if self.linkFilter and u"[[" in entry:
                entry = re.sub(u"\[\[(?:[^]|]+\|)?([^]|]+)\]\]", u"\\1", entry)
            if self.quoteFilter and u"\"" in entry:
                entry = entry.replace(u"\"", u"")
            if self.subscriptFilter and u"<sub>" in entry:
                entry = entry.replace(u"<sub>2</sub>", u"₂") # Engádanse novos valores a medida que sexan necesarios.
            if self.superscriptFilter and u"<sup>" in entry:
                entry = entry.replace(u"<sup>+</sup>", u"⁺") # Engádanse novos valores a medida que sexan necesarios.
            if self.quoteFilter and u"\"" in entry:
                entry = entry.replace(u"\"", u"")
            if self.unescapeHtml and u"&" in entry:
                entry = self.htmlParser.unescape(entry)
            if self.colonFilter and u": " in entry:
                entry = entry.replace(u": ", u" ")

            # Splitters.

            outputEntries = set()
            outputEntries.add(entry)

            if self.basqueFilter: # Nome éuscara oficial, en éuscara e castelán. Por exemplo: «Valle de Trápaga-Trapagaran».
                newOutputEntries = set()
                for outputEntry in outputEntries:
                    if "-" in outputEntry:
                        for newOutputEntry in outputEntry.split("-"):
                            newOutputEntries.add(newOutputEntry)
                    else:
                        newOutputEntries.add(outputEntry)
                outputEntries = newOutputEntries

            if self.commaSplitter:
                newOutputEntries = set()
                for outputEntry in outputEntries:
                    if "," in outputEntry:
                        for newOutputEntry in outputEntry.split(","):
                            newOutputEntries.add(newOutputEntry)
                    else:
                        newOutputEntries.add(outputEntry)
                outputEntries = newOutputEntries

            if self.semicolonSplitter:
                newOutputEntries = set()
                for outputEntry in outputEntries:
                    if ";" in outputEntry:
                        for newOutputEntry in outputEntry.split(";"):
                            newOutputEntries.add(newOutputEntry)
                    else:
                        newOutputEntries.add(outputEntry)
                outputEntries = newOutputEntries

            for separator in self.separatorsSplitter:
                newOutputEntries = set()
                for outputEntry in outputEntries:
                    if separator in outputEntry:
                        for newOutputEntry in outputEntry.split(separator):
                            newOutputEntries.add(newOutputEntry)
                    else:
                        newOutputEntries.add(outputEntry)
                outputEntries = newOutputEntries


            for outputEntry in outputEntries:
                for item in self.applyMandatoryFilters(outputEntry):
                    if self.noRtlFilter and self.isRtl(item):
                        continue
                    yield item