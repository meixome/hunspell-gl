# -*- coding:utf-8 -*-

import re
import pywikibot
import PyICU
import generator


galipedia = pywikibot.Site(u"gl", u"wikipedia")
parenthesis = re.compile(u" *\([^)]*\)")

def getCategoryName(category):
    return category.title()[10:]


class GalipediaGenerator(generator.Generator):

    def __init__(self, resource, partOfSpeech, categoryNames, invalidPagePattern, validCategoryPattern = None,
                 invalidCategoryPattern = None, stripPrefixPattern = None, basqueFilter = False, categoryOfSubcategoriesNames = []):

        self.resource = "galipedia/" + resource
        self.partOfSpeech = partOfSpeech
        self.categoryNames = categoryNames
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

        self.pageNames = set()
        self.visitedCategories = set()


    def addPageName(self, pageName):
        if self.stripPrefixPattern is not None:
            match = self.stripPrefixPattern.match(pageName)
            if match:
                pageName = pageName[len(match.group(0)):]
        self.pageNames.add(pageName)


    def parsePageName(self, pageName):

        pageName = re.sub(parenthesis, u"", pageName) # Eliminar contido entre parénteses.

        if self.invalidPagePattern.match(pageName):
            return

        if " - " in pageName: # Nome en galego e no idioma local. Por exemplo: «Bilbao - Bilbo».
            parts = pageName.split(" - ")
            self.addPageName(parts[0])
        elif "," in pageName: # Datos adicionais para localizar o lugar. Por exemplo: «Durango, País Vasco».
            parts = pageName.split(",")
            self.addPageName(parts[0])
        elif self.basqueFilter is True and "-" in pageName: # Nome éuscara oficial, en éuscara e castelán. Por exemplo: «Valle de Trápaga-Trapagaran».
            parts = pageName.split("-")
            self.addPageName(parts[0])
            self.addPageName(parts[1])
        else:
            self.addPageName(pageName)


    def loadPageNamesFromCategory(self, category):
        print u"Cargando {name}…".format(name=category.title())
        self.visitedCategories.add(getCategoryName(category))
        for subcategory in category.subcategories():
            subcategoryName = getCategoryName(subcategory)
            if subcategoryName not in self.visitedCategories:
                if self.validCategoryPattern is not None and self.validCategoryPattern.match(subcategoryName):
                    self.loadPageNamesFromCategory(subcategory)
                elif self.invalidCategoryPattern is not None and not self.invalidCategoryPattern.match(subcategoryName):
                    self.parsePageName(subcategoryName)

        for page in category.articles():
            pageName = page.title()
            self.parsePageName(pageName)


    def generateFileContent(self):

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
        for name in sorted(self.pageNames, cmp=collator.compare):
            if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
                for ngrama in name.split(u" "):
                    if ngrama not in generator.wordsToIgnore: # N-gramas innecesarios por ser vocabulario galego xeral.
                        content += u"{ngrama} po:{partOfSpeech} [n-grama: {name}]\n".format(ngrama=ngrama, name=name, partOfSpeech=self.partOfSpeech)
            else:
                if name not in generator.wordsToIgnore:
                    content += u"{name} po:{partOfSpeech}\n".format(name=name, partOfSpeech=self.partOfSpeech)
        return content


class GalipediaLocalidadesGenerator(GalipediaGenerator):

    def __init__(self, countryName, categoryNames = [u"Cidades de {name}"]):

        parsedCategoryNames = []
        for categoryName in categoryNames:
            parsedCategoryNames.append(categoryName.format(name=countryName))

        basqueFilter = False
        if countryName == u"España":
            basqueFilter = True

        pattern = u"(Alcaldes|Arquitectura|Capitais|Comunas|Concellos|Imaxes|Galería|Historia|Listas?|Localidades|Lugares|Parroquias|Principais cidades) "
        super(GalipediaLocalidadesGenerator, self).__init__(
            resource = u"onomástica/toponimia/localidades/{name}.dic".format(name=countryName.lower().replace(" ", "-")),
            partOfSpeech = u"topónimo",
            categoryNames = parsedCategoryNames,
            invalidPagePattern = u"^(Modelo:|Wikipedia:|{pattern}[a-z])".format(pattern=pattern),
            validCategoryPattern = u"^(Cidades|Comunas|Concellos|Municipios|Parroquias|Vilas) ",
            invalidCategoryPattern = u"{pattern}[a-z]|.+sen imaxes$".format(pattern=pattern),
            basqueFilter = basqueFilter
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
            invalidPagePattern = u"^(Modelo:|(Batalla|Departamentos|Estados|Lista|Provincias|Rexións|Subrexións) |Comunidade autónoma)",
            validCategoryPattern = u"^(Comarcas|Provincias) ",
            invalidCategoryPattern = u"^(Capitais|Deporte|Estados|Gobernos|Nados|Parlamentos|Políticas|Presidentes|Provincias|Subrexións) ",
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
        resource = u"onomástica/toponimia/accidentes/montañas.dic",
        partOfSpeech = u"topónimo",
        categoryNames = [u"Montañas"],
        invalidPagePattern = u"^(Modelo:)",
        validCategoryPattern = u"^(Cordilleiras|Montañas|Montes)"
        ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/illas.dic",
        partOfSpeech = u"topónimo",
        categoryNames = [u"Illas e arquipélagos", u"Arquipélagos", u"Illas", u"Illas de Asia", u"Illas de Marrocos"],
        categoryOfSubcategoriesNames = [u"Illas por mar", u"Illas por países"],
        invalidPagePattern = u"^(Modelo:|(Batalla|Lista) )",
        invalidCategoryPattern = u"^(Arquipélagos|Illas|Illas de Asia|Illas de Marrocos|Illas galegas|Illas por mar|Illas por países)$"
    ))

    generators.append(GalipediaLocalidadesGenerator(u"Alemaña"))
    generators.append(GalipediaLocalidadesGenerator(u"Alxeria"))
    generators.append(GalipediaLocalidadesGenerator(u"Barbados"))
    generators.append(GalipediaLocalidadesGenerator(u"Bélxica"))
    generators.append(GalipediaLocalidadesGenerator(u"Brasil", [u"Cidades do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Colombia", [u"Cidades de {name}", u"Concellos de {name}", u"Correxementos de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Congo", [u"Cidades do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Eslovaquia"))
    generators.append(GalipediaLocalidadesGenerator(u"España", [u"Concellos de {name}", u"Cidades de {name}", u"Parroquias de Galicia"]))
    generators.append(GalipediaLocalidadesGenerator(u"Estados Unidos de América", [u"Cidades dos {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Etiopía"))
    generators.append(GalipediaLocalidadesGenerator(u"Exipto"))
    generators.append(GalipediaLocalidadesGenerator(u"Francia", [u"Cidades de {name}", u"Comunas de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Grecia"))
    generators.append(GalipediaLocalidadesGenerator(u"Guinea-Bisau"))
    generators.append(GalipediaLocalidadesGenerator(u"Hungría"))
    generators.append(GalipediaLocalidadesGenerator(u"Iemen"))
    generators.append(GalipediaLocalidadesGenerator(u"India", [u"Cidades da {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Indonesia"))
    generators.append(GalipediaLocalidadesGenerator(u"Iraq"))
    generators.append(GalipediaLocalidadesGenerator(u"Israel"))
    generators.append(GalipediaLocalidadesGenerator(u"Italia", [u"Cidades de {name}", u"Comunas de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Líbano", [u"Cidades do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Malí"))
    generators.append(GalipediaLocalidadesGenerator(u"México", [u"Cidades de {name}", u"Cidades prehispánicas de {name}", u"Concellos de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Oceanía"))
    generators.append(GalipediaLocalidadesGenerator(u"Países Baixos", [u"Cidades dos {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Perú"))
    generators.append(GalipediaLocalidadesGenerator(u"Portugal", [u"Cidades de {name}", u"Municipios de {name}", u"Vilas de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Reino Unido", [u"Cidades do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Romanía"))
    generators.append(GalipediaLocalidadesGenerator(u"Serbia"))
    generators.append(GalipediaLocalidadesGenerator(u"Suíza"))
    generators.append(GalipediaLocalidadesGenerator(u"Turquía"))
    generators.append(GalipediaLocalidadesGenerator(u"Venezuela"))
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
        invalidCategoryPattern = u"^(Capitais d|Emperadores$)"
    ))

    generators.append(GalipediaRexionsGenerator(u"Alemaña", [u"Estados de {name}", u"Rexións de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Brasil", [u"Estados do {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Chile"))
    generators.append(GalipediaRexionsGenerator(u"Colombia", [u"Departamentos de {name}", u"Provincias de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"España", [u"Comarcas de {name}", u"Comunidades autónomas de {name}", u"Provincias de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Estados Unidos de América", [u"Estados dos {name}", u"Distritos de Nova York"]))
    generators.append(GalipediaRexionsGenerator(u"Francia", [u"Departamentos de {name}", u"Rexións de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Italia", [u"Rexións de {name}", u"Provincias de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Portugal", [
        u"Antigas provincias portuguesas", u"Distritos e rexións autónomas de Portugal", u"NUTS I portuguesas",
        u"NUTS II portuguesas", u"NUTS III portuguesas", u"Rexións autónomas de Portugal"
    ]))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/zonas/españa.dic",
        partOfSpeech = u"topónimo",
        categoryNames = [u"Barrios de España", u"Distritos de España"],
        invalidPagePattern = u"^Modelo:|(Barrios|Distritos) ",
        validCategoryPattern = u"^(Barrios|Distritos) "
    ))

    return generators