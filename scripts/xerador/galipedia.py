# -*- coding:utf-8 -*-

import os, re, sys
import urllib, urllib2

import pywikibot
from pywikibot.xmlreader import XmlDump

import PyICU
from xdg.BaseDirectory import save_cache_path
from bs4 import BeautifulSoup

import generator


galipedia = pywikibot.Site(u"gl", u"wikipedia")
parenthesis = re.compile(u" *\([^)]*\)")
reference = re.compile(u"< *ref[^>]*>.*?< */ *ref *>")
wikiTags = re.compile(u"\[\[|\]\]")
numberPattern = re.compile(u"^[0-9]+$")
boldPattern = re.compile(u"\'\'\' *(.*?) *\'\'\'")


class DumpProvider(object):

    # Singleton implementation: http://stackoverflow.com/a/1810367
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DumpProvider, cls).__new__(
                                cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance


    def xmlReader(self):
        if not self._xmlReader:
            self._xmlReader = XmlDump(self.pageDumpPath)
        return self._xmlReader


    def getRemoteDumpDate(self):
        request = urllib2.Request(u"http://dumps.wikimedia.org/glwiki/")
        response = urllib2.urlopen(request)
        page = response.read()
        soup = BeautifulSoup(page)
        return int(soup.find_all("tr")[-2].td.a.get_text())


    def __init__(self):

        if self._initialized:
            return
        self._initialized = True

        self._xmlReader = None

        cacheFolder = save_cache_path(u"hunspell-gl")
        dumpFolder = os.path.join(cacheFolder, u"galipedia-dumps")

        pageDumpFileNameTemplate = u"glwiki-{}-pages-meta-current.xml.bz2"
        pageDumpPattern = re.compile(pageDumpFileNameTemplate.format(u"(?P<date>[0-9]{8})"))
        self.pageDumpPath = None

        localDumpDate = None

        needNewDump = True
        remoteDumpDate = self.getRemoteDumpDate()

        if not os.path.exists(dumpFolder):
            os.makedirs(dumpFolder)
        else:
            for filePath in [filePath for filePath in os.listdir(dumpFolder) if os.path.isfile(os.path.join(dumpFolder, filePath))]:
                match = pageDumpPattern.match(filePath)
                if match:
                    localDumpDate = int(match.group(u"date"))
                    self.pageDumpPath = os.path.join(dumpFolder, filePath)
                    break

        if localDumpDate is not None:
            if remoteDumpDate <= localDumpDate:
                needNewDump = False
            else:
                os.remove(self.pageDumpPath)

        if needNewDump:
            pageDumpFileName = pageDumpFileNameTemplate.format(remoteDumpDate)
            self.pageDumpPath = os.path.join(dumpFolder, pageDumpFileName)
            print u"Descargando a copia de seguridade “{}”…".format(self.pageDumpPath),
            sys.stdout.flush()
            urllib.urlretrieve(u"http://dumps.wikimedia.org/glwiki/{}/{}".format(remoteDumpDate, pageDumpFileName), self.pageDumpPath)
            print u"Feito."
            sys.stdout.flush()

def getCategoryName(category):
    return category.title()[10:]

fileTagPattern = re.compile(u"(?i)\[\[ *(File|Image|Ficheiro|Imaxe):([^][]|\[\[[^][]+\]\])+\]\] *")

def removeMediaWikiFileTags(content):
    return fileTagPattern.sub(u"", content)

redirectPattern = re.compile(u"#REDIRECT *\[\[(?P<target>.*)\]\]")

def getPageContent(pageName):
    page = pywikibot.Page(galipedia, pageName)
    while page.isRedirectPage():
        page = page.getRedirectTarget()
    return page.get()

def getFirstSentenceFromPageContent(pageName, pageContent):
    lines = pageContent.split('\n')
    match = redirectPattern.match(lines[0])
    if match:
        return getFirstSentenceFromPageContent(pageName, getPageContent(pageName))
    templateDepth = 0
    for line in lines:
        line = removeMediaWikiFileTags(line)
        line = line.rstrip()
        if len(line) > 0:
            if line[0] not in [' ', '{', '}', '|', '[', ':', '!'] and templateDepth == 0:
                line = re.sub(parenthesis, u"", line) # Eliminar contido entre parénteses.
                line = re.sub(reference, u"", line) # Eliminar contido de referencia.
                return line.split(". ")[0]
            else:
                templateDepth += line.count("{{")
                templateDepth -= line.count("}}")
    return None


class GalipediaGenerator(generator.Generator):

    def __init__(self, resource, partOfSpeech, categoryNames = [], invalidPagePattern = None, validCategoryPattern = None,
                 invalidCategoryPattern = None, stripPrefixPattern = None, basqueFilter = False,
                 categoryOfSubcategoriesNames = [], parsingMode = "Title", pageNames = []):

        self.resource = "galipedia/" + resource
        self.partOfSpeech = partOfSpeech
        self.pageNames = pageNames
        self.categoryNames = categoryNames
        self.parsingMode = parsingMode
        if parsingMode not in ["FirstSentence", "Title"]:
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

        self.dumpProvider = DumpProvider()
        self.firstSentencePages = set()


    def addEntry(self, entry):
        if self.stripPrefixPattern is not None:
            match = self.stripPrefixPattern.match(entry)
            if match:
                entry = entry[len(match.group(0)):]
        entry = entry.strip().replace(u'\ufeff', '') # http://stackoverflow.com/a/6786646
        if entry:
            self.entries.add(entry)


    def parsePageName(self, pageName):

        pageName = re.sub(parenthesis, u"", pageName) # Eliminar contido entre parénteses.

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


    def enqueueToParseFirstSentence(self, pageName):
        self.firstSentencePages.add(pageName)


    def parseFirstSentence(self, pageName, pageContent):
        firstSentence = getFirstSentenceFromPageContent(pageName, pageContent)
        if firstSentence is None:
            print u"First sentence is None in “{}”.".format(pageName)
            raise IndexError
        matches = boldPattern.findall(firstSentence)
        if len(matches) == 0:
            raise ValueError(pageName)
        for match in matches:
            match = re.sub(wikiTags, u"", match) # Eliminar etiquetas MediaWiki, como [[ ou ]].
            self.parsePageName(match)

    mainArticleMatch = re.compile(u"\{\{ *AP *\| *(?P<page>[^|}]+) *(\||\}\})")

    def parseCategory(self, page):
        pageName = getCategoryName(page)
        if self.invalidPagePattern is not None and self.invalidPagePattern.match(pageName):
            return
        if self.parsingMode == "FirstSentence":
            try:
                categoryContent = page.get()
                match = mainArticleMatch.search(categoryContent)
                if match:
                    self.enqueueToParseFirstSentence(match.group("page"))
                    return
            except:
                pass
        self.parsePageName(pageName) # Use category name if anything else fails.


    def parsePage(self, pageName):
        if self.invalidPagePattern is not None and self.invalidPagePattern.match(pageName):
            return
        if self.parsingMode == "FirstSentence":
            try:
                self.enqueueToParseFirstSentence(pageName)
            except:
                self.parsePageName(pageName)
        else:
            self.parsePageName(pageName)


    def loadPageNamesFromCategory(self, category):
        print u"Cargando {name}…".format(name=category.title())
        self.visitedCategories.add(getCategoryName(category))
        for subcategory in category.subcategories():
            subcategoryName = getCategoryName(subcategory)
            if subcategoryName not in self.visitedCategories:
                if self.validCategoryPattern is not None and self.validCategoryPattern.match(subcategoryName):
                    self.loadPageNamesFromCategory(subcategory)
                elif self.invalidCategoryPattern is not None and not self.invalidCategoryPattern.match(subcategoryName):
                    self.parseCategory(subcategory)

        for page in category.articles(namespaces=0):
            self.parsePage(page.title())


    def generateFileContent(self):

        print u"Cargando a copia de seguridade “{}”…".format(self.dumpProvider.pageDumpPath),
        sys.stdout.flush()
        self.xmlReader = self.dumpProvider.xmlReader()
        print u"Feito."
        sys.stdout.flush()

        for pageName in self.pageNames:
            self.parsePage(pageName)
        for categoryName in self.categoryOfSubcategoriesNames:
            category = pywikibot.Category(galipedia, u"Categoría:{}".format(categoryName))
            print u"Cargando subcategorías de {name}…".format(name=category.title())
            for subcategory in category.subcategories():
                self.loadPageNamesFromCategory(subcategory)
        for categoryName in self.categoryNames:
            if categoryName not in self.visitedCategories:
                self.loadPageNamesFromCategory(pywikibot.Category(galipedia, u"Categoría:{}".format(categoryName)))


        if self.parsingMode == "FirstSentence":
            pageCount = len(self.firstSentencePages)
            processedPages = 0
            statement = u"Analizando a primeira oración de cada páxina na copia de seguridade… {} ({}%)\r"
            sys.stdout.write(statement.format(u"{}/{}".format(processedPages, pageCount), processedPages*100/pageCount))
            sys.stdout.flush()
            for entry in self.xmlReader.parse():
                if entry.title in self.firstSentencePages:
                    try:
                        self.parseFirstSentence(entry.title, entry.text)
                    except ValueError:
                        try:
                            pageContent = getPageContent(entry.title)
                            self.parseFirstSentence(entry.title, getPageContent(entry.title))
                        except ValueError:
                            print u"Non se atopou ningunha palabra en letra grosa na primeira oración de «{}»:\n    {}".format(entry.title, getFirstSentenceFromPageContent(entry.title, pageContent))
                            raise
                    self.firstSentencePages.remove(entry.title)
                    processedPages += 1
                    sys.stdout.write(statement.format(u"{}/{}".format(processedPages, pageCount), processedPages*100/pageCount))
                    sys.stdout.flush()
                    if processedPages == pageCount:
                        break
            print
            sys.stdout.flush()

            pageCount = len(self.firstSentencePages)
            if pageCount > 0:
                processedPages = 0
                statement = u"Analizando as páxinas restantes a partir do seu contido no wiki… {} ({}%)\r"
                print statement.format(u"{}/{}".format(processedPages, pageCount), processedPages*100/pageCount),
                sys.stdout.flush()
                for pageName in self.firstSentencePages:
                    self.parseFirstSentence(pageName, getPageContent(pageName))
                    processedPages += 1
                    print statement.format(u"{}/{}".format(processedPages, pageCount), processedPages*100/pageCount),
                    sys.stdout.flush()
                print
                sys.stdout.flush()

        content = ""
        collator = PyICU.Collator.createInstance(PyICU.Locale('gl.UTF-8'))
        for name in sorted(self.entries, cmp=collator.compare):
            if " " in name: # Se o nome contén espazos, usarase unha sintaxe especial no ficheiro .dic.
                ngramas = set()
                for ngrama in name.split(u" "):
                    ngrama = ngrama.replace(u",", u"").strip()
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

        pattern = u"(Alcaldes|Arquitectura|Capitais|Comunas|Concellos|Festas?|Imaxes|Igrexa|Galería|Historia|Listas?|Localidades|Lugares|Municipios|Parroquias|Principais cidades) "
        super(GalipediaLocalidadesGenerator, self).__init__(
            resource = u"onomástica/toponimia/localidades/{name}.dic".format(name=countryName.lower().replace(" ", "-")),
            partOfSpeech = u"topónimo",
            categoryNames = parsedCategoryNames,
            invalidPagePattern = u"(?i)^(Modelo:|Wikipedia:|{pattern}[a-z])".format(pattern=pattern),
            validCategoryPattern = u"(?i)^(Antig[ao]s )?(Cidades|Comunas|Concellos|Municipios|Parroquias|Vilas) ",
            invalidCategoryPattern = u"(?i){pattern}[a-z]|.+sen imaxes$".format(pattern=pattern),
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
            validCategoryPattern = u"^(Comarcas|Departamentos|Estados|Periferias|Provincias|Rexións|Subrexións) ",
            invalidCategoryPattern = u"^(Capitais|Categorías|Deporte|Estados|Gobernos|Nados|Parlamentos|Personalidades|Políticas|Presidentes|Subrexións) ",
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
        categoryNames = [u"Illas e arquipélagos", u"Arquipélagos", u"Atois", u"Illas", u"Illas das Illas Baleares", u"Illas de Galicia", u"Illas de Asia", u"Illas de Marrocos", u"Illas galegas", u"Illas dos Grandes Lagos"],
        categoryOfSubcategoriesNames = [u"Illas e arquipélagos por localización‎", u"Illas por continente", u"Illas por mar", u"Illas por países"],
        invalidPagePattern = u"^(Modelo:|(Batalla|Lista) )",
        invalidCategoryPattern = u"^(Arquipélagos|Illas|Illas da baía d.*|Illas de Alasca|Illas de Asia|Illas de Galicia|Illas de Marrocos|Illas do arquipélago d.*|Illas do Xapón|Illas dos Grandes Lagos|Illas e arquipélagos .*|Illas galegas|Illas por mar|Illas por países|Illas por continente)$"
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
        parsingMode = "FirstSentence"
    ))

    pattern = u"(Afluentes|Regatos|Ríos) "
    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/ríos.dic",
        partOfSpeech = u"topónimo",
        categoryOfSubcategoriesNames = [u"Ríos"],
        invalidPagePattern = u"^(Modelo:|{pattern}|(Galería de imaxes|Hidrografía|Lista) |(Caneiro \(muíño\)|Pasadoiro|Pontella \(pasaxe\))$)".format(pattern=pattern),
        invalidCategoryPattern = u"^({pattern}|Imaxes)".format(pattern=pattern),
        validCategoryPattern = u"^{pattern}".format(pattern=pattern),
        parsingMode = "FirstSentence"
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
    generators.append(GalipediaLocalidadesGenerator(u"Emiratos Árabes Unidos", [u"Cidades dos {name}"], parsingMode="FirstSentence"))
    generators.append(GalipediaLocalidadesGenerator(u"Eslovaquia"))
    generators.append(GalipediaLocalidadesGenerator(u"España", [u"Concellos de {name}", u"Cidades de {name}", u"Parroquias de Galicia"], parsingMode="FirstSentence"))
    generators.append(GalipediaLocalidadesGenerator(u"Estados Unidos de América", [u"Cidades dos {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Etiopía"))
    generators.append(GalipediaLocalidadesGenerator(u"Exipto"))
    generators.append(GalipediaLocalidadesGenerator(u"Finlandia", parsingMode="FirstSentence"))
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
    generators.append(GalipediaLocalidadesGenerator(u"Perú", [u"Cidades do {name}"]))
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
    generators.append(GalipediaLocalidadesGenerator(u"Xapón", [u"Concellos do {name}"], parsingMode="FirstSentence"))
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
        parsingMode = "FirstSentence"
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