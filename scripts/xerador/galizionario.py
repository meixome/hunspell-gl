# -*- coding:utf-8 -*-

import re
import pywikibot
import PyICU
import generator


galizionario = pywikibot.Site(u"gl", u"wiktionary")

def getCategoryName(category):
    return category.title()[10:]

def getPageName(page):
    if page.isCategory():
        return getCategoryName(page)
    else:
        return page.title()


class GalizionarioGenerator(generator.Generator):

    def __init__(self, resource, partOfSpeech, pageNames = [], categoryNames = []):

        self.resource = "galizionario/" + resource
        self.partOfSpeech = partOfSpeech
        self.pageNames = pageNames
        self.categoryNames = categoryNames
        self.entries = set()
        self.visitedCategories = set()


    def addEntry(self, entry):
        self.entries.add(entry)


    def parsePageName(self, pageName):
        self.addEntry(pageName)


    def parsePage(self, page):
        self.parsePageName(getPageName(page))


    def loadPageNamesFromCategory(self, category):
        print u"Cargando {name}…".format(name=category.title())
        self.visitedCategories.add(getCategoryName(category))
        for page in category.articles(namespaces=0):
            self.parsePage(page)


    def generateFileContent(self):

        for pageName in self.pageNames:
            self.parsePage(pywikibot.Page(galizionario, pageName))

        for categoryName in self.categoryNames:
            if categoryName not in self.visitedCategories:
                self.loadPageNamesFromCategory(pywikibot.Category(galizionario, u"Categoría:{}".format(categoryName)))

        content = ""
        collator = PyICU.Collator.createInstance(PyICU.Locale('gl.UTF-8'))
        for name in sorted(self.entries, cmp=collator.compare):
            if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
                for ngrama in name.split(u" "):
                    ngrama = ngrama.replace(u",", u"")
                    if ngrama not in generator.wordsToIgnore: # N-gramas innecesarios por ser vocabulario galego xeral.
                        content += u"{ngrama} po:{partOfSpeech} [n-grama: {name}]\n".format(ngrama=ngrama, name=name, partOfSpeech=self.partOfSpeech)
            else:
                if name not in generator.wordsToIgnore:
                    content += u"{name} po:{partOfSpeech}\n".format(name=name, partOfSpeech=self.partOfSpeech)
        return content



def loadGeneratorList():

    generators = []

    generators.append(GalizionarioGenerator(
        resource = u"toponimia/xeral.dic",
        partOfSpeech = u"topónimo",
        categoryNames = [u"Toponimia en galego"]
    ))

    generators.append(GalizionarioGenerator(
        resource = u"toponimia/galicia.dic",
        partOfSpeech = u"topónimo",
        categoryNames = [u"Toponimia de Galicia en galego"]
    ))

    # TODO: Desenvolver un sistema de determinación das liñas correctas de feminino e plural para o Hunspell.
    # Por exemplo: «capixaba/10» para «capixaba/s».
    #generators.append(GalizionarioGenerator(
        #resource = u"xentilicio/xeral.dic",
        #partOfSpeech = u"xentilicio",
        #categoryNames = [u"Xentilicio en galego"]
    #))

    return generators