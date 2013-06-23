# -*- coding:utf-8 -*-

import codecs, pywikibot, re, sys
import galipedia as common


def parsePageName(pageName):
    if not invalidPagePattern.match(pageName):
        pageName = re.sub(parenthesis, u"", pageName) # Eliminar contido entre parénteses.
        if u" - " in pageName: # Nome en galego e no idioma local. Por exemplo: «Bilbao - Bilbo».
            parts = pageName.split(u" - ")
            locationNames.add(parts[0])
        elif u"," in pageName: # Datos adicionais para localizar o lugar. Por exemplo: «Durango, País Vasco».
            parts = pageName.split(u",")
            locationNames.add(parts[0])
        else:
            locationNames.add(pageName)


def loadLocationsFromCategoryAndSubcategories(category):

    print u"Cargando {name}…".format(name=category.title())

    for subcategory in category.subcategories():
        if not invalidCategoryPattern.match(subcategory.title()):
            parsePageName(subcategory.title().split(":")[1])

    for page in category.articles():
        pageName = page.title()
        parsePageName(pageName)


# Lóxica principal:

categoryNames = [u"Illas e arquipélagos", u"Arquipélagos", u"Illas", u"Illas de Asia", u"Illas de Marrocos"]
categoryOfSubcategoriesNames = [u"Illas por mar", u"Illas por países"]
outputFileName = u"illas.dic"

parenthesis = re.compile(u" *\([^)]*\)")

locationNames = set()
galipedia = pywikibot.Site(u"gl", u"wikipedia")
invalidPagePattern = re.compile(u"^(Modelo:|(Batalla|Lista) )")
invalidCategoryPattern = re.compile(u"^(Arquipélagos|Illas|Illas de Asia|Illas de Marrocos|Illas galegas|Illas por mar|Illas por países)$")

for categoryName in categoryNames:
    loadLocationsFromCategoryAndSubcategories(pywikibot.Category(galipedia, u"Categoría:{}".format(categoryName)))

for categoryName in categoryOfSubcategoriesNames:
    category = pywikibot.Category(galipedia, u"Categoría:{}".format(categoryName))
    print u"Cargando {name}…".format(name=category.title())
    for subcategory in category.subcategories():
        loadLocationsFromCategoryAndSubcategories(subcategory)

dicFileContent = ""
for name in sorted(locationNames):
    if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
        for ngrama in name.split(u" "):
            if ngrama not in common.wordsToIgnore: # N-gramas innecesarios por ser vocabulario galego xeral.
                dicFileContent += u"{ngrama} po:topónimo [n-grama: {name}]\n".format(ngrama=ngrama, name=name)
    else:
        if name not in common.wordsToIgnore:
            dicFileContent += u"{name} po:topónimo\n".format(name=name)

with codecs.open(outputFileName, u"w", u"utf-8") as fileObject:
    fileObject.write(dicFileContent)
