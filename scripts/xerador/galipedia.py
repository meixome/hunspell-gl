# -*- coding:utf-8 -*-

import re
import pywikibot
import PyICU
import generator


galipedia = pywikibot.Site(u"gl", u"wikipedia")
parenthesis = re.compile(u" *\([^)]*\)")
reference = re.compile(u"< *ref[^>]*>.*?< */ *ref *>")
wikiTags = re.compile(u"\[\[|\]\]")
numberPattern = re.compile(u"^[0-9]+$")

def getCategoryName(category):
    return category.title()[10:]

def getFirstSencenteFromPageContent(pageContent):
    lines = pageContent.split('\n')
    withinTemplate = False
    for line in lines:
        if len(line) > 0:
            if line[0] not in [' ', '{', '}', '|', '[', ':', '!'] and withinTemplate is False:
                line = re.sub(parenthesis, u"", line) # Eliminar contido entre parénteses.
                line = re.sub(reference, u"", line) # Eliminar contido de referencia.
                return line.split(". ")[0]
            elif line[:2] == u"{{":
                if line[-2:] != u"}}":
                    withinTemplate = True
            elif line[:2] == u"}}":
                withinTemplate = False
    return None

def getPageName(page):
    if page.isCategory():
        return getCategoryName(page)
    else:
        return page.title()


class GalipediaGenerator(generator.Generator):

    def __init__(self, resource, partOfSpeech, categoryNames = [], invalidPagePattern = None, validCategoryPattern = None,
                 invalidCategoryPattern = None, stripPrefixPattern = None, basqueFilter = False,
                 categoryOfSubcategoriesNames = [], parsingMode = "Title", pageNames = []):

        self.resource = "galipedia/" + resource
        self.partOfSpeech = partOfSpeech
        self.pageNames = pageNames
        self.categoryNames = categoryNames
        self.parsingMode = parsingMode
        if parsingMode not in ["FirstSencente", "Title"]:
            print "Warning: Unsupported parsing mode: {mode}".format(mode=parsingMode)

        if invalidPagePattern is None:
            self.invalidPagePattern = invalidPagePattern
        else:
            self.invalidPagePattern = re.compile(invalidPagePattern)

        # Patrón que deben seguir as subcategorías para que se cargue o seu contido ao atopalas dentro dunha categoría.
        if validCategoryPattern is None:
            self.validCategoryPattern = validCategoryPattern
        else:
            self.validCategoryPattern = re.compile(validCategoryPattern)

        # Se unha categoría non coincide con «validCategoryPattern» pero si con este patrón, cárgase como un nome de páxina.
        if invalidCategoryPattern is None:
            self.invalidCategoryPattern = invalidCategoryPattern
        else:
            self.invalidCategoryPattern = re.compile(invalidCategoryPattern)

        # Se o nome dunha páxina cadra co patrón, a parte que cadre suprímese. Permite, por exemplo, que «Provincia de
        # X» se transforme en simplemente «X» indicando unha expresión que coincida con «Provincia de».
        if stripPrefixPattern is None:
            self.stripPrefixPattern = stripPrefixPattern
        else:
            self.stripPrefixPattern = re.compile(stripPrefixPattern)

        self.basqueFilter = basqueFilter # Os nomes (de topónimos éuscaras) como «Valle de Trápaga-Trapagaran» dan lugar a dúas entradas, «Valle de Trápaga» e «Trapagaran».
        self.categoryOfSubcategoriesNames = categoryOfSubcategoriesNames # Lista de categorías das que cargar subcategorías directamente, sen filtrar o nome das subcategorías con «validCategoryPattern».

        self.entries = set()
        self.visitedCategories = set()


    def addEntry(self, entry):
        if self.stripPrefixPattern is not None:
            match = self.stripPrefixPattern.match(entry)
            if match:
                entry = entry[len(match.group(0)):]
        self.entries.add(entry)


    def parsePageName(self, pageName):

        pageName = re.sub(parenthesis, u"", pageName).strip() # Eliminar contido entre parénteses.

        if self.invalidPagePattern is not None and self.invalidPagePattern.match(pageName):
            return

        if " - " in pageName: # Nome en galego e no idioma local. Por exemplo: «Bilbao - Bilbo».
            parts = pageName.split(" - ")
            self.addEntry(parts[0])
        elif "," in pageName: # Datos adicionais para localizar o lugar. Por exemplo: «Durango, País Vasco».
            parts = pageName.split(",")
            self.addEntry(parts[0])
        elif self.basqueFilter is True and "-" in pageName: # Nome éuscara oficial, en éuscara e castelán. Por exemplo: «Valle de Trápaga-Trapagaran».
            parts = pageName.split("-")
            self.addEntry(parts[0])
            self.addEntry(parts[1])
        else:
            self.addEntry(pageName)


    def parseFirstSencente(self, pageContent):
        firstSentence = getFirstSencenteFromPageContent(pageContent)
        if firstSentence is None:
            raise Exception
        boldEntry = re.compile(u"\'\'\'(.*?)\'\'\'")
        matches = boldEntry.findall(firstSentence)
        if len(matches) == 0:
            raise Exception
        for match in matches:
            match = re.sub(wikiTags, u"", match) # Eliminar etiquetas MediaWiki, como [[ ou ]].
            self.addEntry(match)


    def parsePage(self, page):
        if self.parsingMode == "FirstSencente":
            if page.isCategory():
                categoryName = getCategoryName(page)
                page = pywikibot.Page(galipedia, categoryName)
                try:
                    self.parseFirstSencente(page.get())
                except:
                    self.parsePageName(categoryName)
            else:
                try:
                    self.parseFirstSencente(page.get())
                except: # Páxina sen contido, como [[Imperio do Xapón]] o día 27/07/2013.
                    self.parsePageName(page.title())
        else:
            self.parsePageName(getPageName(page))


    def loadPageNamesFromCategory(self, category):
        print u"Cargando {name}…".format(name=category.title())
        self.visitedCategories.add(getCategoryName(category))
        for subcategory in category.subcategories():
            subcategoryName = getCategoryName(subcategory)
            if subcategoryName not in self.visitedCategories:
                if self.validCategoryPattern is not None and self.validCategoryPattern.match(subcategoryName):
                    self.loadPageNamesFromCategory(subcategory)
                elif self.invalidCategoryPattern is not None and not self.invalidCategoryPattern.match(subcategoryName):
                    self.parsePage(subcategory)

        for page in category.articles(namespaces=0):
            self.parsePage(page)


    def generateFileContent(self):

        for pageName in self.pageNames:
            self.parsePage(pywikibot.Page(galipedia, pageName))

        for categoryName in self.categoryOfSubcategoriesNames:
            category = pywikibot.Category(galipedia, u"Categoría:{}".format(categoryName))
            print u"Cargando subcategorías de {name}…".format(name=category.title())
            for subcategory in category.subcategories():
                self.loadPageNamesFromCategory(subcategory)

        for categoryName in self.categoryNames:
            if categoryName not in self.visitedCategories:
                self.loadPageNamesFromCategory(pywikibot.Category(galipedia, u"Categoría:{}".format(categoryName)))

        content = ""
        collator = PyICU.Collator.createInstance(PyICU.Locale('gl.UTF-8'))
        for name in sorted(self.entries, cmp=collator.compare):
            if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
                ngramas = set()
                for ngrama in name.split(u" "):
                    ngrama = ngrama.replace(u",", u"")
                    if ngrama not in generator.wordsToIgnore and ngrama not in ngramas and not numberPattern.match(ngrama): # N-gramas innecesarios por ser vocabulario galego xeral.
                        ngramas.add(ngrama)
                        content += u"{ngrama} po:{partOfSpeech} [n-grama: {name}]\n".format(ngrama=ngrama, name=name, partOfSpeech=self.partOfSpeech)
            else:
                if name not in generator.wordsToIgnore:
                    content += u"{name} po:{partOfSpeech}\n".format(name=name, partOfSpeech=self.partOfSpeech)
        return content


class GalipediaLocalidadesGenerator(GalipediaGenerator):

    def __init__(self, countryName, categoryNames = [u"Cidades de {name}"], parsingMode = "Title"):

        parsedCategoryNames = []
        for categoryName in categoryNames:
            parsedCategoryNames.append(categoryName.format(name=countryName))

        basqueFilter = False
        if countryName == u"España":
            basqueFilter = True

        pattern = u"(Alcaldes|Arquitectura|Capitais|Comunas|Concellos|Imaxes|Galería|Historia|Listas?|Localidades|Lugares|Municipios|Parroquias|Principais cidades) "
        super(GalipediaLocalidadesGenerator, self).__init__(
            resource = u"onomástica/toponimia/localidades/{name}.dic".format(name=countryName.lower().replace(" ", "-")),
            partOfSpeech = u"topónimo",
            categoryNames = parsedCategoryNames,
            invalidPagePattern = u"^(Modelo:|Wikipedia:|{pattern}[a-z])".format(pattern=pattern),
            validCategoryPattern = u"^(Cidades|Comunas|Concellos|Municipios|Parroquias|Vilas) ",
            invalidCategoryPattern = u"{pattern}[a-z]|.+sen imaxes$".format(pattern=pattern),
            basqueFilter = basqueFilter,
            parsingMode = parsingMode
        )


class GalipediaRexionsGenerator(GalipediaGenerator):

    def __init__(self, countryName, categoryNames = [u"Rexións de {name}"]):

        parsedCategoryNames = []
        for categoryName in categoryNames:
            parsedCategoryNames.append(categoryName.format(name=countryName))

        super(GalipediaRexionsGenerator, self).__init__(
            resource = u"onomástica/toponimia/rexións/{name}.dic".format(name=countryName.lower().replace(" ", "-")),
            partOfSpeech = u"topónimo",
            categoryNames = parsedCategoryNames,
            invalidPagePattern = u"^(Modelo:|(Batalla|Departamentos|Estados|Lista|Periferias|Provincias|Rexións|Subrexións) |Comunidade autónoma)",
            validCategoryPattern = u"^(Comarcas|Periferias|Provincias) ",
            invalidCategoryPattern = u"^(Capitais|Categorías|Deporte|Estados|Gobernos|Nados|Parlamentos|Políticas|Presidentes|Subrexións) ",
            stripPrefixPattern = u"^(Estado|Provincia)( autónom[ao])? d(a|as|e|o|os) "
        )



def loadGeneratorList():

    generators = []

    pattern = u"(Arquitectura relixiosa|Basílicas|Capelas|Catedrais|Colexiatas|Conventos|Ermidas|Igrexas|Mosteiros|Mosteiros e conventos|Pórticos|Santuarios|Templos) "
    generators.append(GalipediaGenerator(
        resource = u"onomástica/arquitectura/relixión.dic",
        partOfSpeech = u"nome propio",
        categoryNames = [u"Arquitectura relixiosa por países"],
        invalidPagePattern = u"^(Modelo:|{pattern}|Galería de imaxes)".format(pattern=pattern),
        validCategoryPattern = u"^{pattern}".format(pattern=pattern),
        invalidCategoryPattern = u"^(Imaxes) "
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/astronomía/planetas.dic",
        partOfSpeech = u"nome propio",
        categoryNames = [u"Planetas"],
        invalidPagePattern = u"^(Lista d|Planeta anano$|Planeta($| ))",
        validCategoryPattern = u"^(Candidatos a planeta|Planetas |Plutoides$)",
        invalidCategoryPattern = u"^Sistemas planetarios$"
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/arte/escultura/relixión.dic",
        partOfSpeech = u"nome propio",
        categoryNames = [u"Escultura relixiosa de Galicia"],
        validCategoryPattern = u"^(Baldaquinos d|Cruceiros d)",
        invalidCategoryPattern = u"^Imaxes d"
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/illas.dic",
        partOfSpeech = u"topónimo",
        categoryNames = [u"Illas e arquipélagos", u"Arquipélagos", u"Atois", u"Illas", u"Illas de Asia", u"Illas de Marrocos", u"Illas das Illas Baleares", u"Illas dos Grandes Lagos"],
        categoryOfSubcategoriesNames = [u"Illas e arquipélagos por localización‎", u"Illas e arquipélagos por país", u"Illas por mar", u"Illas por países"],
        invalidPagePattern = u"^(Modelo:|(Batalla|Lista) )",
        invalidCategoryPattern = u"^(Arquipélagos|Illas|Illas da baía d.*|Illas de Asia|Illas de Marrocos|Illas do arquipélago d.*|Illas do Xapón|Illas dos Grandes Lagos|Illas e arquipélagos .*|Illas galegas|Illas por mar|Illas por países)$"
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/montañas.dic",
        partOfSpeech = u"topónimo",
        categoryNames = [u"Montañas"],
        invalidPagePattern = u"^(Modelo:)",
        validCategoryPattern = u"^(Cordilleiras|Montañas|Montes)"
    ))

    pattern = u"(Praias) "
    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/praias.dic",
        partOfSpeech = u"topónimo",
        categoryNames = [u"Praias"],
        invalidPagePattern = u"^(Modelo:|{pattern}|Bandeira Azul$|Galería de imaxes|Praia$|Praia nudista$)".format(pattern=pattern),
        validCategoryPattern = u"^{pattern}".format(pattern=pattern),
        invalidCategoryPattern = u"^(Imaxes) "
    ))

    pattern = u"(Rexións) "
    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/rexións.dic",
        partOfSpeech = u"topónimo",
        categoryNames = [u"Rexións de Europa"],
        invalidPagePattern = u"^(Modelo:|{pattern}|Galería de imaxes)".format(pattern=pattern),
        validCategoryPattern = u"^{pattern}".format(pattern=pattern),
        invalidCategoryPattern = u"^(Imaxes) ",
        pageNames = [
            u"Cisxordania",
            u"Cochinchina",
            u"Dalmacia",
            u"Faixa de Gaza"
        ],
        parsingMode = "FirstSencente"
    ))

    pattern = u"(Afluentes|Regatos|Ríos) "
    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/ríos.dic",
        partOfSpeech = u"topónimo",
        categoryOfSubcategoriesNames = [u"Ríos"],
        invalidPagePattern = u"^(Modelo:|{pattern}|(Galería de imaxes|Hidrografía|Lista) )".format(pattern=pattern),
        invalidCategoryPattern = u"^({pattern}|Imaxes)".format(pattern=pattern),
        validCategoryPattern = u"^{pattern}".format(pattern=pattern)
    ))

    generators.append(GalipediaLocalidadesGenerator(u"Desaparecidas", [u"Cidades desaparecidas"])) # Localidades desaparecidas.
    generators.append(GalipediaLocalidadesGenerator(u"Alemaña"))
    generators.append(GalipediaLocalidadesGenerator(u"Alxeria"))
    generators.append(GalipediaLocalidadesGenerator(u"Bangladesh"))
    generators.append(GalipediaLocalidadesGenerator(u"Barbados"))
    generators.append(GalipediaLocalidadesGenerator(u"Bélxica"))
    generators.append(GalipediaLocalidadesGenerator(u"Bolivia"))
    generators.append(GalipediaLocalidadesGenerator(u"Brasil", [u"Cidades do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Colombia", [u"Cidades de {name}", u"Concellos de {name}", u"Correxementos de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Congo", [u"Cidades da República do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Cuba"))
    generators.append(GalipediaLocalidadesGenerator(u"Dinamarca"))
    generators.append(GalipediaLocalidadesGenerator(u"Emiratos Árabes Unidos", [u"Cidades dos {name}"], parsingMode="FirstSencente"))
    generators.append(GalipediaLocalidadesGenerator(u"Eslovaquia"))
    generators.append(GalipediaLocalidadesGenerator(u"España", [u"Concellos de {name}", u"Cidades de {name}", u"Parroquias de Galicia"]))
    generators.append(GalipediaLocalidadesGenerator(u"Estados Unidos de América", [u"Cidades dos {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Etiopía"))
    generators.append(GalipediaLocalidadesGenerator(u"Exipto"))
    generators.append(GalipediaLocalidadesGenerator(u"Finlandia"))
    generators.append(GalipediaLocalidadesGenerator(u"Francia", [u"Cidades de {name}", u"Comunas de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Grecia"))
    generators.append(GalipediaLocalidadesGenerator(u"Grecia antiga", [u"Antigas cidades gregas"]))
    generators.append(GalipediaLocalidadesGenerator(u"Guatemala", [u"Cidades de {name}", u"Municipios de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Guinea-Bisau"))
    generators.append(GalipediaLocalidadesGenerator(u"Hungría"))
    generators.append(GalipediaLocalidadesGenerator(u"Iemen"))
    generators.append(GalipediaLocalidadesGenerator(u"India", [u"Cidades da {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Indonesia"))
    generators.append(GalipediaLocalidadesGenerator(u"Iraq"))
    generators.append(GalipediaLocalidadesGenerator(u"Irlanda"))
    generators.append(GalipediaLocalidadesGenerator(u"Israel"))
    generators.append(GalipediaLocalidadesGenerator(u"Italia", [u"Cidades de {name}", u"Comunas de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Líbano", [u"Cidades do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Malí"))
    generators.append(GalipediaLocalidadesGenerator(u"México", [u"Cidades de {name}", u"Cidades prehispánicas de {name}", u"Concellos de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Oceanía"))
    generators.append(GalipediaLocalidadesGenerator(u"Países Baixos", [u"Cidades dos {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Perú"))
    generators.append(GalipediaLocalidadesGenerator(u"Polonia"))
    generators.append(GalipediaLocalidadesGenerator(u"Portugal", [u"Cidades de {name}", u"Municipios de {name}", u"Vilas de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Qatar"))
    generators.append(GalipediaLocalidadesGenerator(u"Reino Unido", [u"Cidades do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Romanía"))
    generators.append(GalipediaLocalidadesGenerator(u"Serbia"))
    generators.append(GalipediaLocalidadesGenerator(u"Siria"))
    generators.append(GalipediaLocalidadesGenerator(u"Suráfrica"))
    generators.append(GalipediaLocalidadesGenerator(u"Suíza"))
    generators.append(GalipediaLocalidadesGenerator(u"Timor Leste"))
    generators.append(GalipediaLocalidadesGenerator(u"Turquía"))
    generators.append(GalipediaLocalidadesGenerator(u"Venezuela"))
    generators.append(GalipediaLocalidadesGenerator(u"Xapón", [u"Concellos do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Xordania"))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/lugares/galicia.dic",
        partOfSpeech = u"topónimo",
        categoryNames = [u"Lugares de Galicia", u"Parroquias de Galicia"],
        invalidPagePattern = u"^(Lugares d|Parroquias d)",
        validCategoryPattern = u"^(Lugares d|Parroquias d)"
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/países.dic",
        partOfSpeech = u"topónimo",
        categoryNames = [
            u"Estados desaparecidos",
            u"Países con recoñecemento limitado",
            u"Países de América",
            u"Países de Asia",
            u"Países de Europa",
            u"Países de Oceanía",
            u"Países de África"
        ],
        invalidPagePattern = u"^(Modelo:|Concellos |Galería d|Historia d|Lista d|Principais cidades )",
        validCategoryPattern = u"^(Estados desaparecidos d|Imperios|Países d)",
        invalidCategoryPattern = u"^(Capitais d|Emperadores$)",
        parsingMode = "FirstSencente"
    ))

    generators.append(GalipediaRexionsGenerator(u"Alemaña", [u"Estados de {name}", u"Rexións de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Brasil", [u"Estados do {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Chile"))
    generators.append(GalipediaRexionsGenerator(u"Colombia", [u"Departamentos de {name}", u"Provincias de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"España", [u"Comarcas de {name}", u"Comunidades autónomas de {name}", u"Provincias de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Estados Unidos de América", [u"Estados dos {name}", u"Distritos de Nova York"]))
    generators.append(GalipediaRexionsGenerator(u"Finlandia"))
    generators.append(GalipediaRexionsGenerator(u"Francia", [u"Departamentos de {name}", u"Rexións de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Grecia", [u"Periferias de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Italia", [u"Rexións de {name}", u"Provincias de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"México", [u"Estados de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Países Baixos", [u"Provincias dos {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Portugal", [
        u"Antigas provincias portuguesas", u"Distritos e rexións autónomas de Portugal", u"NUTS I portuguesas",
        u"NUTS II portuguesas", u"NUTS III portuguesas", u"Rexións autónomas de Portugal"
    ]))
    generators.append(GalipediaRexionsGenerator(u"Rusia", [u"Repúblicas de {name}"]))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/zonas/españa.dic",
        partOfSpeech = u"topónimo",
        categoryNames = [u"Barrios de España", u"Distritos de España"],
        invalidPagePattern = u"^Modelo:|(Barrios|Distritos) ",
        validCategoryPattern = u"^(Barrios|Distritos) "
    ))

    return generators