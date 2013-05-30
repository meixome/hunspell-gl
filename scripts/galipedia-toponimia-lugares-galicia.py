# -*- coding:utf-8 -*-

import codecs, pywikibot, re, sys


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


# Lóxica principal:

ngramasToIgnore = (
    # Nexos comúns.
    u"A", u"As", u"O", u"Os", u"da", u"das", u"de", u"do", u"dos", u"e",

    # Substantivos comúns correctos en galego.
    u"Campo", u"Campos",
    u"Castelo", u"Castelos",
    u"Cidade", u"Cidades",
    u"Costa", u"Costas",
    u"Faro", u"Faros",
    u"Nova", u"Novas", u"Novo", u"Novos",
    u"Ponte", u"Pontes",
    u"Porto", u"Portos",
    u"Ribeira", u"Ribeiras",
    u"Río", u"Ríos",
    u"San", u"Santa", u"Santas", u"Santo", u"Santos",
    u"Torre", u"Torres",
    u"Val", u"Vales",
    u"Vila", u"Vilas"
    )

locationNames = set()
galipedia = pywikibot.Site(u"gl", u"wikipedia")
category = pywikibot.Category(galipedia, u"Categoría:{}".format("Lugares de Galicia"))
invalidPagePattern = re.compile(u"^Lugares de")
validCategoryPattern = re.compile(u"^Categoría:Lugares de")
loadLocationsFromCategoryAndSubcategories(category)

dicFileContent = ""
for name in sorted(locationNames):
    if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
        for ngrama in name.split(u" "):
            if ngrama not in ngramasToIgnore: # N-gramas innecesarios por ser vocabulario galego xeral.
                dicFileContent += u"{ngrama} po:topónimo [n-grama: {name}]\n".format(ngrama=ngrama, name=name)
    else:
        dicFileContent += u"{name} po:topónimo\n".format(name=name)

with codecs.open("galicia.dic", u"w", u"utf-8") as fileObject:
    fileObject.write(dicFileContent)
