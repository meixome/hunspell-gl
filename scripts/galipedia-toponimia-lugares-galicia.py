# -*- coding:utf-8 -*-

import codecs, pywikibot, re, sys
import galipedia as common


def loadLocationsFromCategoryAndSubcategories(category):

    print u"Cargando {name}…".format(name=category.title())

    for subcategory in category.subcategories():
        if validCategoryPattern.match(subcategory.title()):
            loadLocationsFromCategoryAndSubcategories(subcategory)

    for page in category.articles():
        pageName = page.title()
        if not invalidPagePattern.match(pageName):
            parts = pageName.split(",")
            locationNames.add(parts[0])


locationNames = set()
galipedia = pywikibot.Site(u"gl", u"wikipedia")
invalidPagePattern = re.compile(u"^(Lugares d|Parroquias d)")
validCategoryPattern = re.compile(u"^Categoría:(Lugares d|Parroquias d)")
for categoryName in [u"Lugares de Galicia", u"Parroquias de Galicia"]:
    loadLocationsFromCategoryAndSubcategories(pywikibot.Category(galipedia, u"Categoría:{}".format(categoryName)))

dicFileContent = ""
for name in sorted(locationNames):
    if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
        for ngrama in name.split(u" "):
            if ngrama not in common.wordsToIgnore and ngrama != "-":
                dicFileContent += u"{ngrama} po:topónimo [n-grama: {name}]\n".format(ngrama=ngrama, name=name)
    else:
        if name not in common.wordsToIgnore:
            dicFileContent += u"{name} po:topónimo\n".format(name=name)

with codecs.open("galicia.dic", u"w", u"utf-8") as fileObject:
    fileObject.write(dicFileContent)
