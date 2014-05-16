# -*- coding:utf-8 -*-

import re, string, sys
import pywikibot
import PyICU
import generator
import unicodedata


numberPattern = re.compile(u"^[0-9]+$")

def getCategoryName(category):
    return category.title()[10:]

def getPageName(page):
    if page.isCategory():
        return getCategoryName(page)
    else:
        return page.title()


class CategoryBrowser():

    def __init__(self, site=None, categoryNames=[], ignoreCategoryNames=[]):
        self.site = site
        self.categoryNames = categoryNames
        self.ignoreCategoryNames = ignoreCategoryNames
        self.visitedCategories = set()
        self.pagesToIgnore = set()


    def setSite(self, site):
        self.site = site


    def parsePageName(self, pageName):
        if pageName not in self.pagesToIgnore:
            yield pageName


    def parsePage(self, page):
        for entry in self.parsePageName(getPageName(page)):
            yield entry


    def loadPageNamesFromCategory(self, category):
        print u"Cargando {name}…".format(name=category.title())
        self.visitedCategories.add(getCategoryName(category))
        for page in category.articles(namespaces=0):
            for entry in self.parsePage(page):
                yield entry


    def loadPageNamesFromCategoryIntoIgnoreList(self, category):
        print u"Cargando {name} para omitir o seu contido…".format(name=category.title())
        self.visitedCategories.add(getCategoryName(category))
        for page in category.articles(namespaces=0):
            self.pagesToIgnore.add(getPageName(page))


    def run(self):

        for categoryName in self.ignoreCategoryNames:
            if categoryName not in self.visitedCategories:
                self.loadPageNamesFromCategoryIntoIgnoreList(pywikibot.Category(self.site, u"Category:{}".format(categoryName)))

        for categoryName in self.categoryNames:
            if categoryName not in self.visitedCategories:
                for entry in self.loadPageNamesFromCategory(pywikibot.Category(self.site, u"Category:{}".format(categoryName))):
                    yield entry


class ListParser():
    """Parses the content of a list page using a regular expression, and yields
    results.
    """
    def __init__(self, namePattern, pageNames, site=None, ignorePattern=None):

        regexType = type(re.compile(u"."))

        if not isinstance(namePattern, regexType):
            namePattern = re.compile(namePattern)
        self.namePattern = namePattern

        if ignorePattern and not isinstance(ignorePattern, regexType):
            ignorePattern = re.compile(ignorePattern)
        self.ignorePattern = ignorePattern

        self.site = site
        self.pageNames = pageNames


    def setSite(self, site):
        self.site = site

    def isRtl(self, text):
        return len([None for character in text if unicodedata.bidirectional(character) in ('R', 'AL')])/float(len(text)) > 0.1


    def parse(self, pageContent):
        for line in pageContent.splitlines():
            match = self.namePattern.match(line)
            if match:
                name = match.group(u"name")
                if self.ignorePattern and self.ignorePattern.match(name):
                    continue
                if self.isRtl(name):
                    continue
                yield name


    def run(self):
        processedPages = 0
        pageCount = len(self.pageNames)
        statement = u"Analizando as listas das páxinas… {} ({}%)\r"
        sys.stdout.write(statement.format(u"{}/{}".format(processedPages, pageCount), processedPages*100/pageCount))
        sys.stdout.flush()
        for pageName in self.pageNames:
            page = pywikibot.Page(self.site, pageName)
            pageContent = page.get()
            for entry in self.parse(pageContent):
                yield entry
            processedPages += 1
            sys.stdout.write(statement.format(u"{}/{}".format(processedPages, pageCount), processedPages*100/pageCount))
            sys.stdout.flush()
        print
        sys.stdout.flush()


class WiktionaryGenerator(generator.Generator):

    def __init__(self, languageCode, resource, partOfSpeech, yielders = []):

        self.resource = "wiktionary/{}/{}".format(languageCode, resource)
        self.partOfSpeech = partOfSpeech
        self.entries = set()
        self.site = pywikibot.Site(languageCode, u"wiktionary")

        self.yielders = yielders
        for yielder in self.yielders:
            yielder.setSite(self.site)


    def addEntry(self, entry):
        self.entries.add(entry)


    def parsePageName(self, pageName):
        if pageName not in self.pagesToIgnore:
            self.addEntry(pageName)


    def parsePage(self, page):
        self.parsePageName(getPageName(page))


    def loadPageNamesFromCategory(self, category):
        print u"Cargando {name}…".format(name=category.title())
        self.visitedCategories.add(getCategoryName(category))
        for page in category.articles(namespaces=0):
            self.parsePage(page)


    def loadPageNamesFromCategoryIntoIgnoreList(self, category):
        print u"Cargando {name} para omitir o seu contido…".format(name=category.title())
        self.visitedCategories.add(getCategoryName(category))
        for page in category.articles(namespaces=0):
            self.pagesToIgnore.add(getPageName(page))


    def entriesAsHunspellDictionary(self):
        print u"Xerando o ficheiro de saída (con {} entradas)…".format(len(self.entries)),
        sys.stdout.flush()
        content = ""
        collator = PyICU.Collator.createInstance(PyICU.Locale('gl.UTF-8'))
        for name in sorted(self.entries, cmp=collator.compare):
            if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
                ngramas = set()
                for ngrama in name.split(u" "):
                    ngrama = ngrama.replace(u",", u"").strip()
                    if ngrama not in generator.wordsToIgnore and ngrama not in ngramas and not numberPattern.match(ngrama): # N-gramas innecesarios por ser vocabulario galego xeral.
                        ngramas.add(ngrama)
                        content += u"{ngrama} po:{partOfSpeech} [n-grama: {name}]\n".format(ngrama=ngrama, name=name, partOfSpeech=self.partOfSpeech)
            else:
                if name not in generator.wordsToIgnore:
                    content += u"{name} po:{partOfSpeech}\n".format(name=name, partOfSpeech=self.partOfSpeech)
        print u"Feito."
        sys.stdout.flush()
        return content


    def generateFileContent(self):
        for yielder in self.yielders:
            for entry in yielder.run():
                self.entries.add(entry)
        return self.entriesAsHunspellDictionary()


class GalizionarioGenerator(WiktionaryGenerator):

    def __init__(self, resource, partOfSpeech, yielders=[]):
        super(GalizionarioGenerator, self).__init__(
                "gl",
                resource,
                partOfSpeech,
                yielders=yielders
            )


class WiktionaryEnGenerator(WiktionaryGenerator):

    def __init__(self, resource, partOfSpeech, yielders=[]):
        super(WiktionaryEnGenerator, self).__init__(
                "en",
                resource,
                partOfSpeech,
                yielders=yielders
            )


class WiktionaryEnNamesGenerator(WiktionaryGenerator):

    def __init__(self):
        namePattern = re.compile(u"^: *(\'\'\')? *\[\[ *([^]|]+\|)? *(?P<name>[^]|]+) *\]\]")
        ignorePattern = re.compile(u"^-")
        pageNames = []
        for pagePrefix in [u"Appendix:Female given names/", u"Appendix:Male given names/"]:
            for letter in list(string.ascii_uppercase):
                pageNames.append(pagePrefix + letter)
        listParser = ListParser(namePattern, pageNames, ignorePattern=ignorePattern)
        super(WiktionaryEnNamesGenerator, self).__init__(
                "en",
                "antroponimia.dic",
                u"antropónimo",
                yielders=[listParser,]
            )



def loadGeneratorList():

    generators = []


    # Galizionario.

    generators.append(GalizionarioGenerator(
        resource = u"toponimia/xeral.dic",
        partOfSpeech = u"topónimo",
        yielders = [
                CategoryBrowser(
                        categoryNames = [u"Toponimia en galego"],
                        ignoreCategoryNames = [u"Toponimia de Galicia en galego"]
                    ),
            ]
    ))

    generators.append(GalizionarioGenerator(
        u"toponimia/galicia.dic",
        u"topónimo",
        yielders=[
                CategoryBrowser(
                        categoryNames = [u"Toponimia de Galicia en galego"]
                    ),
            ]
    ))


    # Wiktionary en inglés.

    generators.append(WiktionaryEnNamesGenerator())


    # TODO: Desenvolver un sistema de determinación das liñas correctas de feminino e plural para o Hunspell.
    # Por exemplo: «capixaba/10» para «capixaba/s».
    #generators.append(GalizionarioGenerator(
        #resource = u"xentilicio/xeral.dic",
        #partOfSpeech = u"xentilicio",
        #categoryNames = [u"Xentilicio en galego"]
    #))

    return generators
