# -*- coding:utf-8 -*-

import codecs, pywikibot, re, sys
import galipedia as common


def parseCountryName(name):

    # Valores predeterminados.
    categoryNames = []
    outputFileName = u"{filename}.dic".format(filename=name.lower().replace(" ", "-"))

    if name in [u"Brasil"]:
        categoryNames = [
            u"Estados do {name}".format(name=name)
        ]
    if name in [u"Italia"]:
        categoryNames = [
            u"Rexións de {name}".format(name=name),
            u"Provincias de {name}".format(name=name)
        ]

    return categoryNames, outputFileName


def loadLocationsFromCategoryAndSubcategories(category):

    print u"Cargando {name}…".format(name=category.title())

    for subcategory in category.subcategories():
        if validCategoryPattern.match(subcategory.title()):
            loadLocationsFromCategoryAndSubcategories(subcategory)

    for page in category.articles():
        pageName = page.title()
        if not invalidPagePattern.match(pageName):
            if " - " in pageName: # Nome en galego e no idioma local. Por exemplo: «Bilbao - Bilbo».
                parts = pageName.split(" - ")
                locationNames.add(parts[0])
            elif "-" in pageName: # Nome éuscara oficial, en éuscara e castelán. Por exemplo: «Valle de Trápaga-Trapagaran».
                parts = pageName.split("-")
                locationNames.add(parts[0])
                locationNames.add(parts[1])
            elif "," in pageName: # Datos adicionais para localizar o lugar. Por exemplo: «Durango, País Vasco».
                parts = pageName.split(",")
                locationNames.add(parts[0])
            else:
                locationNames.add(pageName)


# Lóxica principal:

if len(sys.argv) != 2:
    print "A forma correcta de executar o script é:"
    print "    galipedia-toponimia-rexións.py <estado>"
    print
    print "O estados que se saben compatíbeis son:"
    print "    Brasil, Italia."
    sys.exit()

categoryNames, outputFileName = parseCountryName(sys.argv[1].decode('UTF-8'))

namePrefixes = re.compile(u"Provincia( autónoma)? d(a|as|e|o|os) ")

locationNames = set()
galipedia = pywikibot.Site(u"gl", u"wikipedia")
invalidPagePattern = re.compile(u"^(Modelo:|Provincias d)")
validCategoryPattern = re.compile(u"^Categoría:(Provincias) ")

for categoryName in categoryNames:
    loadLocationsFromCategoryAndSubcategories(pywikibot.Category(galipedia, u"Categoría:{}".format(categoryName)))


dicFileContent = ""
for name in sorted(locationNames):
    match = namePrefixes.match(name)
    if match:
        name = name[len(match.group(0)):]
    if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
        for ngrama in name.split(u" "):
            if ngrama not in common.ngramasToIgnore: # N-gramas innecesarios por ser vocabulario galego xeral.
                dicFileContent += u"{ngrama} po:topónimo [n-grama: {name}]\n".format(ngrama=ngrama, name=name)
    else:
        dicFileContent += u"{name} po:topónimo\n".format(name=name)

with codecs.open(outputFileName, u"w", u"utf-8") as fileObject:
    fileObject.write(dicFileContent)
