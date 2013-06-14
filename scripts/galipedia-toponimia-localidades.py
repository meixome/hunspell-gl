# -*- coding:utf-8 -*-

import codecs, pywikibot, re, sys
import galipedia as common


def parseCountryName(name):

    # Valores predeterminados, correctos polo menos para «España».
    categoryNames = [
        u"Concellos de {name}".format(name=name),
        u"Cidades de {name}".format(name=name)
    ]
    outputFileName = u"{filename}.dic".format(filename=name.lower().replace(" ", "-"))

    if name in [u"Estados Unidos de América"]:
        categoryNames = [u"Cidades dos {name}".format(name=name)]
    elif name in [u"Etiopía", u"Iemen", u"Israel", u"Oceanía"]:
        categoryNames = [u"Cidades de {name}".format(name=name)]
    elif name in [u"México"]:
        categoryNames = [
            u"Cidades de {name}".format(name=name),
            u"Cidades prehispánicas de {name}".format(name=name),
            u"Concellos de {name}".format(name=name)
        ]
    elif name in [u"Portugal"]:
        categoryNames = [
            u"Cidades de {name}".format(name=name),
            u"Municipios de {name}".format(name=name),
            u"Vilas de {name}".format(name=name)
        ]
    elif name in [u"Reino Unido"]:
        categoryNames = [u"Cidades do {name}".format(name=name)]

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
    print "    galipedia-toponimia-localidades.py <estado>"
    print
    print "O estados e continentes que se saben compatíbeis son:"
    print "    España, Estados Unidos de América, Etiopía, Iemen, Israel, México, Oceanía, Portugal, Reino Unido."
    sys.exit()

categoryNames, outputFileName = parseCountryName(sys.argv[1].decode('UTF-8'))

nameSuffixes = re.compile(" \([^)]+\)$")

locationNames = set()
galipedia = pywikibot.Site(u"gl", u"wikipedia")
invalidPagePattern = re.compile(u"^(Modelo:|Concellos |Galería d|Historia d|Lista d|Principais cidades )")
validCategoryPattern = re.compile(u"^Categoría:(Cidades|Comunas|Concellos|Vilas) ")

for categoryName in categoryNames:
    loadLocationsFromCategoryAndSubcategories(pywikibot.Category(galipedia, u"Categoría:{}".format(categoryName)))


dicFileContent = ""
for name in sorted(locationNames):
    match = nameSuffixes.search(name)
    if match:
        name = name[:-len(match.group(0))]
    if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
        for ngrama in name.split(u" "):
            if ngrama not in common.wordsToIgnore: # N-gramas innecesarios por ser vocabulario galego xeral.
                dicFileContent += u"{ngrama} po:topónimo [n-grama: {name}]\n".format(ngrama=ngrama, name=name)
    else:
        if name not in common.wordsToIgnore:
            dicFileContent += u"{name} po:topónimo\n".format(name=name)

with codecs.open(outputFileName, u"w", u"utf-8") as fileObject:
    fileObject.write(dicFileContent)
