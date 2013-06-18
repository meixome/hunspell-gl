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
    elif name in [u"Chile"]:
        categoryNames = [
            u"Rexións de {name}".format(name=name)
        ]
    elif name in [u"Colombia"]:
        categoryNames = [
            u"Departamentos de {name}".format(name=name),
            u"Provincias de {name}".format(name=name)
        ]
    elif name in [u"España"]:
        categoryNames = [
            u"Comarcas de {name}".format(name=name),
            u"Comunidades autónomas de {name}".format(name=name),
            u"Provincias de {name}".format(name=name)
        ]
    elif name in [u"Estados Unidos de América"]:
        categoryNames = [
            u"Estados dos {name}".format(name=name)
        ]
    elif name in [u"Francia"]:
        categoryNames = [
            u"Departamentos de {name}".format(name=name),
            u"Rexións de {name}".format(name=name)
        ]
    elif name in [u"Italia"]:
        categoryNames = [
            u"Rexións de {name}".format(name=name),
            u"Provincias de {name}".format(name=name)
        ]
    elif name in [u"Portugal"]:
        categoryNames = [
            u"Antigas provincias portuguesas",
            u"Distritos e rexións autónomas de Portugal",
            u"NUTS I portuguesas",
            u"NUTS II portuguesas",
            u"NUTS III portuguesas",
            u"Rexións autónomas de Portugal"
        ]

    return categoryNames, outputFileName


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
    print "    galipedia-toponimia-rexións.py <estado>"
    print
    print "O estados que se saben compatíbeis son:"
    print "    Brasil, Colombia, España, Estados Unidos de América, Francia, Italia, Portugal."
    sys.exit()

categoryNames, outputFileName = parseCountryName(sys.argv[1].decode('UTF-8'))

namePrefixes = re.compile(u"Provincia( autónoma)? d(a|as|e|o|os) ")
parenthesis = re.compile(u" *\([^)]*\)")

locationNames = set()
galipedia = pywikibot.Site(u"gl", u"wikipedia")
invalidPagePattern = re.compile(u"^(Modelo:|(Batalla|Departamentos|Estados|Lista|Provincias|Rexións|Subrexións) |Comunidade autónoma)")
validCategoryPattern = re.compile(u"^Categoría:(Comarcas|Provincias) ")
invalidCategoryPattern = re.compile(u"^(Capitais|Deporte|Estados|Gobernos|Nados|Parlamentos|Políticas|Presidentes|Provincias|Subrexións) ")

for categoryName in categoryNames:
    loadLocationsFromCategoryAndSubcategories(pywikibot.Category(galipedia, u"Categoría:{}".format(categoryName)))


dicFileContent = ""
for name in sorted(locationNames):
    match = namePrefixes.match(name)
    if match:
        name = name[len(match.group(0)):]
    if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
        for ngrama in name.split(u" "):
            if ngrama not in common.wordsToIgnore: # N-gramas innecesarios por ser vocabulario galego xeral.
                dicFileContent += u"{ngrama} po:topónimo [n-grama: {name}]\n".format(ngrama=ngrama, name=name)
    else:
        if name not in common.wordsToIgnore:
            dicFileContent += u"{name} po:topónimo\n".format(name=name)

with codecs.open(outputFileName, u"w", u"utf-8") as fileObject:
    fileObject.write(dicFileContent)
