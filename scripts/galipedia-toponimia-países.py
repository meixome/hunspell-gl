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
            if "-" in pageName: # Nome en galego e no idioma local. Por exemplo: «Bilbao - Bilbo».
                parts = pageName.split("-")
                locationNames.add(parts[0].strip())
            elif "," in pageName: # Datos adicionais para localizar o lugar. Por exemplo: «Durango, País Vasco».
                parts = pageName.split(",")
                locationNames.add(parts[0])
            else:
                locationNames.add(pageName)


# Lóxica principal:

nameSuffixes = re.compile(" \([^)]+\)$")

categoryNames = [
    u"Estados desaparecidos",
    u"Países con recoñecemento limitado",
    u"Países de América",
    u"Países de Asia",
    u"Países de Europa",
    u"Países de Oceanía",
    u"Países de África"
]
outputFileName = u"países.dic"

locationNames = set()
galipedia = pywikibot.Site(u"gl", u"wikipedia")
invalidPagePattern = re.compile(u"^(Modelo:|Concellos |Galería d|Historia d|Lista d|Principais cidades )")
validCategoryPattern = re.compile(u"^Categoría:(Estados desaparecidos d|Imperios|Países d)")

for categoryName in categoryNames:
    loadLocationsFromCategoryAndSubcategories(pywikibot.Category(galipedia, u"Categoría:{}".format(categoryName)))


dicFileContent = ""
for name in sorted(locationNames):
    match = nameSuffixes.search(name)
    if match:
        name = name[:-len(match.group(0))]
    if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
        for ngrama in name.split(u" "):
            if ngrama not in common.ngramasToIgnore: # N-gramas innecesarios por ser vocabulario galego xeral.
                dicFileContent += u"{ngrama} po:topónimo [n-grama: {name}]\n".format(ngrama=ngrama, name=name)
    else:
        dicFileContent += u"{name} po:topónimo\n".format(name=name)

with codecs.open(outputFileName, u"w", u"utf-8") as fileObject:
    fileObject.write(dicFileContent)
