# -*- coding:utf-8 -*-

import codecs, pywikibot, re, sys
import galipedia as common


def parseCountryName(name):

    # Valores predeterminados.
    categoryNames = []
    outputFileName = u"{filename}.dic".format(filename=name.lower().replace(" ", "-"))

    if name in [u"España"]:
        categoryNames = [
            u"Concellos de {name}".format(name=name),
            u"Cidades de {name}".format(name=name),
            u"Parroquias de Galicia"
        ]
    elif name in [u"Estados Unidos de América", u"Países Baixos"]:
        categoryNames = [u"Cidades dos {name}".format(name=name)]
    elif name in [u"Alemaña", u"Alxeria", u"Etiopía", u"Exipto", u"Grecia", u"Iemen", u"Indonesia", u"Iraq", u"Israel", u"Malí",
                  u"Oceanía", u"Perú", u"Serbia", u"Suíza", u"Turquía", u"Xordania"]:
        categoryNames = [u"Cidades de {name}".format(name=name)]
    elif name in [u"Líbano"]:
        categoryNames = [u"Cidades do {name}".format(name=name)]
    elif name in [u"Francia"]:
        categoryNames = [
            u"Cidades de {name}".format(name=name),
            u"Comunas de {name}".format(name=name)
        ]
    elif name in [u"Italia"]:
        categoryNames = [
            u"Comunas de {name}".format(name=name)
        ]
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


def parsePageName(pageName):
    if not invalidPagePattern.match(pageName):

        if u"," in pageName: # Datos adicionais para localizar o lugar. Por exemplo: «Durango, País Vasco».
            pageName = pageName.split(",")[0]

        if u" - " in pageName: # Nome en galego e no idioma local. Por exemplo: «Bilbao - Bilbo».
            pageName = pageName.split(" - ")[0]

        if u"-" in pageName and countryName == u"España": # Nome éuscara oficial, en éuscara e castelán. Por exemplo: «Valle de Trápaga-Trapagaran».
            parts = pageName.split(u"-")
            locationNames.add(parts[0])
            locationNames.add(parts[1])
        else:
            locationNames.add(pageName)


def loadLocationsFromCategoryAndSubcategories(category):
    print u"Cargando {name}…".format(name=category.title())
    for subcategory in category.subcategories():
        if validCategoryPattern.match(subcategory.title()):
            loadLocationsFromCategoryAndSubcategories(subcategory)
        elif not invalidCategoryPattern.match(subcategory.title()):
            parsePageName(subcategory.title().split(":")[1])
    for page in category.articles():
        pageName = page.title()
        parsePageName(pageName)


# Lóxica principal:

if len(sys.argv) != 2:
    print "A forma correcta de executar o script é:"
    print "    galipedia-toponimia-localidades.py <estado>"
    print
    print "O estados e continentes que se saben compatíbeis son:"
    print "    Alemaña, Alxeria, España, Estados Unidos de América, Etiopía, Exipto, Francia, Grecia, Iemen, Indonesia, Iraq,"
    print "    Israel, Italia, Líbano, Malí, México, Oceanía, Países Baixos, Perú, Portugal, Reino Unido, Serbia,"
    print "    Suíza, Turquía, Xordania."
    sys.exit()

countryName = sys.argv[1].decode('UTF-8')
categoryNames, outputFileName = parseCountryName(countryName)

nameSuffixes = re.compile(" \([^)]+\)$")

locationNames = set()
galipedia = pywikibot.Site(u"gl", u"wikipedia")
invalidPagePattern = re.compile(u"^(Modelo:|Wikipedia:|(Alcaldes|Arquitectura|Capitais|Comunas|Concellos|Imaxes|Galería|Historia|Listas?|Localidades|Lugares|Parroquias|Principais cidades) [a-z])")
validCategoryPattern = re.compile(u"^Categoría:(Cidades|Comunas|Concellos|Municipios|Parroquias|Vilas) ")
invalidCategoryPattern = re.compile(u"(Alcaldes|Arquitectura|Capitais|Comunas|Concellos|Imaxes|Galería|Historia|Listas?|Localidades|Lugares|Parroquias|Principais cidades) [a-z]|.+sen imaxes$")

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
