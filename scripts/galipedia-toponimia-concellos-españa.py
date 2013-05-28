# -*- coding:utf-8 -*-

import codecs, pywikibot, re



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

ngramasToIgnore = (u"A", u"Campo", u"Campos", u"de", u"do", u"Río", u"Ríos", u"San", u"Torre", u"Torres")
locationNames = set()
galipedia = pywikibot.Site(u"gl", u"wikipedia")
category = pywikibot.Category(galipedia, u"Categoría:Concellos de España")
invalidPagePattern = re.compile(u"^(Modelo:|Lista de (concellos|municipios)|Galería de escudos|Concellos )")
validCategoryPattern = re.compile(u"^Categoría:Concellos ")
loadLocationsFromCategoryAndSubcategories(category)

dicFileContent = ""
for name in sorted(locationNames):
    if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
        for ngrama in name.split(u" "):
            if ngrama not in ngramasToIgnore: # N-gramas innecesarios por ser vocabulario galego xeral.
                dicFileContent += u"{ngrama} po:topónimo [n-grama: {name}]\n".format(ngrama=ngrama, name=name)
    else:
        dicFileContent += u"{name} po:topónimo\n".format(name=name)

with codecs.open(u"españa.dic", u"w", u"utf-8") as fileObject:
    fileObject.write(dicFileContent)
