# -*- coding:utf-8 -*-

from mediawiki import MediaWikiGenerator  # Dictionary generators.
from mediawiki import EntryGenerator  # Entry generators.
from mediawiki import PageLoader, CategoryBrowser  # Page generators.
from mediawiki import TitleParser, FirstSentenceParser, LineParser, TableParser  # Page parsers.
from mediawiki import EntryParser  # Page parsers.


# Wikipedia generator.

class WikipediaGenerator(MediaWikiGenerator):

    def __init__(self, languageCode, resource, partOfSpeech, entryGenerators):
        super(WikipediaGenerator, self).__init__(
                siteName=u"wikipedia",
                languageCode=languageCode,
                resource=resource,
                partOfSpeech=partOfSpeech,
                entryGenerators=entryGenerators,
            )




# Language-specific Wikipedia generators.

class GalipediaGenerator(WikipediaGenerator):

    def __init__(self, resource, partOfSpeech, entryGenerators):
        super(GalipediaGenerator, self).__init__(
                "gl",
                resource,
                partOfSpeech,
                entryGenerators=entryGenerators,
            )



class WikipediaEnGenerator(WikipediaGenerator):

    def __init__(self, resource, partOfSpeech, entryGenerators):
        super(WikipediaEnGenerator, self).__init__(
                "en",
                resource,
                partOfSpeech,
                entryGenerators=entryGenerators,
            )


class WikipediaEsGenerator(WikipediaGenerator):

    def __init__(self, resource, partOfSpeech, entryGenerators):
        super(WikipediaEsGenerator, self).__init__(
                "es",
                resource,
                partOfSpeech,
                entryGenerators=entryGenerators,
            )


class WikipediaHuGenerator(WikipediaGenerator):

    def __init__(self, resource, partOfSpeech, entryGenerators):
        super(WikipediaHuGenerator, self).__init__(
                "hu",
                resource,
                partOfSpeech,
                entryGenerators=entryGenerators,
            )


class WikipediaPtGenerator(WikipediaGenerator):

    def __init__(self, resource, partOfSpeech, entryGenerators):
        super(WikipediaPtGenerator, self).__init__(
                "pt",
                resource,
                partOfSpeech,
                entryGenerators=entryGenerators,
            )




# Helpers.

class GalipediaLocalidadesGenerator(GalipediaGenerator):

    def __init__(self, countryName, categoryNames = [u"Cidades de {name}"], pageParser=None):

        parsedCategoryNames = []
        for categoryName in categoryNames:
            parsedCategoryNames.append(categoryName.format(name=countryName))

        pattern = u"(Alcaldes|Arquitectura|Capitais|Comunas|Concellos|Festas?|Imaxes|Igrexa|Galería|Historia|Listas?|Localidades|Lugares|Municipios|Parroquias|Principais cidades) "
        categoryBrowser = CategoryBrowser(
            categoryNames=parsedCategoryNames,
            invalidPagePattern = u"(?i)^(Wikipedia:|{pattern}[a-z])".format(pattern=pattern),
            validCategoryPattern = u"(?i)^(Antig[ao]s )?(Cidades|Comunas|Concellos|Municipios|Parroquias|Vilas) ",
            invalidCategoryAsPagePattern = u"(?i){pattern}[a-z]|.+sen imaxes$".format(pattern=pattern),
        )

        entryParser = EntryParser()
        if countryName == u"España":
            entryParser = EntryParser(basqueFilter=True)

        super(GalipediaLocalidadesGenerator, self).__init__(
            resource = u"onomástica/toponimia/localidades/{name}.dic".format(name=countryName.lower().replace(" ", "-")),
            partOfSpeech = u"topónimo",
            entryGenerators=[
                EntryGenerator(
                    pageGenerators=[categoryBrowser,],
                    pageParser=pageParser,
                    entryParser=entryParser,
                )
            ],
        )



class GalipediaRexionsGenerator(GalipediaGenerator):

    def __init__(self, countryName, categoryNames = [u"Rexións de {name}"], pageParser=None):

        parsedCategoryNames = []
        for categoryName in categoryNames:
            parsedCategoryNames.append(categoryName.format(name=countryName))

        categoryPattern = u"Áreas municipais|Comarcas|Condados|Departamentos|Distritos|Divisións|Estados|Partidos xudiciais|Periferias|Provincias|Repúblicas|Rexións|Subdivisións|Subrexións"
        categoryBrowser = CategoryBrowser(
            categoryNames=parsedCategoryNames,
            invalidPagePattern = u"^((Batalla|Lista|{}) |Comunidade autónoma)".format(categoryPattern),
            validCategoryPattern = u"^({}) ".format(categoryPattern),
            invalidCategoryAsPagePattern = u"^(Capitais|Categorías|Concellos|Deporte|Gobernos|Nados|Parlamentos|Personalidades|Políticas|Presidentes) ",
        )

        super(GalipediaRexionsGenerator, self).__init__(
            resource = u"onomástica/toponimia/rexións/{name}.dic".format(name=countryName.lower().replace(" ", "-")),
            partOfSpeech = u"topónimo",
            entryGenerators=[
                EntryGenerator(
                    pageGenerators=[categoryBrowser,],
                    pageParser=pageParser,
                )
            ],
        )



class GalipediaNamesGenerator(GalipediaGenerator):

    def __init__(self):

        pageNames = [u"Lista de nomes masculinos en galego", u"Lista de nomes femininos en galego"]
        pageLoader = PageLoader(pageNames=pageNames)

        categoryBrowser = CategoryBrowser(
            categoryNames = [u"Antroponimia",],
            invalidPagePattern = u"^(Antroponimia$|Lista )",
            invalidCategoryPattern = u"^Identidade$",
        )

        namePattern = u"^\* *\'\'\' *(\[\[)? *([^]|]+\| *)?(?P<entry>[^]|]+) *(\]\])? *\'\'\'"
        lineParser = LineParser(namePattern)

        super(GalipediaNamesGenerator, self).__init__(
            resource = u"onomástica/antroponimia/xeral.dic",
            partOfSpeech = u"antropónimo",
            entryGenerators = [
                EntryGenerator(
                    pageGenerators=[pageLoader,],
                    pageParser=lineParser,
                ),
                EntryGenerator(
                    pageGenerators=[categoryBrowser,],
                    pageParser=FirstSentenceParser(),
                ),
            ]
        )



def loadGeneratorList():

    generators = []


    # Galipedia

    generators.append(GalipediaGenerator(
        resource = u"bioquímica.dic",
        partOfSpeech = u"substantivo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Coencimas",],
                        invalidCategoryPattern = u"^Personalidades",
                    ),
                ],
                pageParser = FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/administración/intelixencia.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Servizos de intelixencia"],
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/administración/ministerios.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Ministerios de España"],
                        validCategoryPattern = u"^Antigos ministerios"
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    pattern = u"Grafiteiros|Personalidades|Pintores"
    generators.append(GalipediaGenerator(
        resource = u"onomástica/antroponimia/arte/pintura.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Personalidades da pintura"],
                        invalidPagePattern = u"^(Imaxes |Listas |Premio |{})".format(pattern),
                        validCategoryPattern = u"^({})".format(pattern),
                    ),
                ],
                pageParser = FirstSentenceParser(),
            )
        ],
    ))

    pattern = u"Biólogos|Bioquímicos|Científicos|Empresarios|Farmacéuticos|Físicos|Matemáticos|Médicos|Personalidades|Químicos"
    generators.append(GalipediaGenerator(
        resource = u"onomástica/antroponimia/ciencia.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Personalidades da ciencia"],
                        invalidPagePattern = u"^(Día do Científico|Imaxes |Premio |{})".format(pattern),
                        validCategoryPattern = u"^({})".format(pattern),
                    ),
                ],
                pageParser = FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/antroponimia/países/costa-rica.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [
                            u"Presidentes de Costa Rica",
                        ],
                        invalidPagePattern = u"^Presidente de Costa Rica$",
                    ),
                ],
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/antroponimia/países/españa.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [
                            u"Escritores de Galicia",
                            u"Finados en 1975",
                            u"Nados en Pontedeume",
                            u"Nados en Salceda de Caselas",
                            u"Reis de Galicia",
                            u"Vicepresidentes do goberno de España",
                        ],
                        invalidPagePattern = u"^(Dinastía|Imaxes de|Lista d|Xeración)",
                        validCategoryPattern = u"^(Dinastía|Escritores|Poetas|Tradutores|Reis|Xeración)",
                        invalidCategoryAsPagePattern = u"^(Lista d)",
                    ),
                ],
                pageParser = FirstSentenceParser(),
            )
        ],
    ))

    pattern = u"Chanceleres|Personalidades|Políticos|Presidente do Consello de Comisarios do Pobo|Presidentes|Primeiros [Mm]inistros|Secretarios|Taoiseach"
    generators.append(GalipediaGenerator(
        resource = u"onomástica/antroponimia/política/primeiros-ministros.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Primeiros ministros"],
                        invalidPagePattern = u"^(Imaxes |Listas |Premio |{})".format(pattern),
                        validCategoryPattern = u"^({})".format(pattern),
                    ),
                ],
                pageParser = FirstSentenceParser(),
            )
        ],
    ))

    pattern = u"Actores|Personalidades|Xornalistas"
    generators.append(GalipediaGenerator(
        resource = u"onomástica/antroponimia/radio.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Personalidades da radio"],
                        invalidPagePattern = u"^(Imaxes |Premio |{})".format(pattern),
                        validCategoryPattern = u"^({})".format(pattern),
                    ),
                ],
                pageParser = FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/antroponimia/relixión.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [
                            u"Personaxes bíblicos",
                        ],
                        invalidPagePattern = u"^Apóstolo$",
                        validCategoryPattern = u"^Apóstolos",
                    ),
                ],
                pageParser = FirstSentenceParser(),
            )
        ],
    ))

    pattern = u"Presentadores"
    generators.append(GalipediaGenerator(
        resource = u"onomástica/antroponimia/televisión/presentadores.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Presentadores de televisión"],
                        invalidPagePattern = u"^(Imaxes |Listas |Premio |{})".format(pattern),
                        validCategoryPattern = u"^({})".format(pattern),
                    ),
                ],
                pageParser = FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaNamesGenerator())

    pattern = u"(Arquitectura relixiosa|Basílicas|Capelas|Catedrais|Colexiatas|Conventos|Ermidas|Igrexas|Mosteiros|Mosteiros e conventos|Pórticos|Santuarios|Templos) "
    generators.append(GalipediaGenerator(
        resource = u"onomástica/arquitectura/relixión.dic",
        partOfSpeech = u"nome propio",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Arquitectura relixiosa por países"],
                        invalidPagePattern = u"^({pattern}|Galería de imaxes|Iglesias gallegas de la Edad Media$)".format(pattern=pattern),
                        validCategoryPattern = u"^{pattern}".format(pattern=pattern),
                        invalidCategoryAsPagePattern = u"^(Imaxes) ",
                    ),
                ],
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/arte/escultura/relixión.dic",
        partOfSpeech = u"nome propio",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Escultura relixiosa de Galicia"],
                        validCategoryPattern = u"^(Baldaquinos d|Cruceiros d)",
                        invalidCategoryAsPagePattern = u"^Imaxes d",
                    ),
                ],
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/astronomía/planetas.dic",
        partOfSpeech = u"nome propio",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Planetas"],
                        invalidPagePattern = u"^(Lista d|Planeta anano$|Planeta($| ))",
                        validCategoryPattern = u"^(Candidatos a planeta|Planetas |Plutoides$)",
                        invalidCategoryAsPagePattern = u"^Sistemas planetarios$",
                    ),
                ],
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/deporte/acontecementos.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Eventos deportivos"],
                        validCategoryPattern = u"^(Acontecementos|Campionatos|Competicións|Ligas|Mundiais|Torneos)",
                        invalidCategoryAsPagePattern = u"(^(Balóns|Goleadores|Tempadas)|.* nos Xogos Olímpicos$)",
                        invalidPagePattern = u".*\d+-\d+",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/deporte/fórmula1/escuderías.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Escuderías de Fórmula 1"],
                        validCategoryPattern = u"^(Escuderías)",
                        invalidPagePattern = u"^Lista",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/economía/feiras.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Institucións feirais",],
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/economía/índices-bolsistas.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Índices bolsistas",],
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/economía/empresas/banca.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Bancos e caixas de aforro"],
                        invalidPagePattern = u"^(Banca ética|Banco malo|Caixa de aforros|Caixeiro automático)$",
                        validCategoryPattern = u"^(Bancos|Caixas)",
                        invalidCategoryAsPagePattern = u"^(Personalidades)",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/economía/empresas/telecomunicacións.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryOfPagesNames = [u"Empresas de telecomunicacións"],
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/historia/acontecementos.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Acontecementos históricos"],
                        validCategoryPattern = u"^(Atentados|Golpes de estado)",
                        invalidCategoryAsPagePattern = u"^(Catástrofes|Conflitos|Declaracións de independencia|Guerras|Revolucións)", # Ignorados, polos menos de momento.
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/historia/civilizacións.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Civilizacións"],
                        invalidPagePattern = u"^((Lista|Pobos) |(Civilización|Cultura dos Campos de Urnas|Sala do hidromel)$)",
                        validCategoryPattern = u"^(Pobos|Reinos) ",
                        invalidCategoryAsPagePattern = u"^(Arquitectura|Xeografía) ",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    pattern = u"Linguaxes"
    generators.append(GalipediaGenerator(
        resource = u"onomástica/informática/linguaxes.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Linguaxes informáticas"],
                        invalidPagePattern = u"^(Imaxes |Listas |Exemplos |Linguaxe compilada|Linguaxe de alto nivel|Linguaxe de programación$|Linguaxe interpretada|{})".format(pattern),
                        validCategoryPattern = u"^({})".format(pattern),
                    ),
                ],
                pageParser = FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/informática/sistemas-de-almacenamento.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Sistemas de almacenamento"],
                        invalidPagePattern = u"^Administrador de base de datos$",
                    ),
                ],
                pageParser = FirstSentenceParser(),
            )
        ],
    ))

    pattern = u"Redes sociais|Weblogs|Wikipedias|Xornais"
    generators.append(GalipediaGenerator(
        resource = u"onomástica/informática/sitios-de-internet.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Sitios de internet"],
                        invalidPagePattern = u"^(Imaxes |Listas |(Rede social|Blogueiros)$|{})".format(pattern),
                        validCategoryPattern = u"^({})".format(pattern),
                        invalidCategoryAsPagePattern = u"^Blogueiros$"
                    ),
                ],
                pageParser = FirstSentenceParser(),
            )
        ],
    ))

    pattern = u"Ambientes de escritorio|Aplicacións|Compañías|Conxuntos de aplicacións|Editores|Emuladores|Follas|Kernels|Navegadores|Personaxes|Procesadores|Reprodutores|Servidores|Sistemas operativos|Software|Utilidades|Videoxogos|Xestores"
    generators.append(GalipediaGenerator(
        resource = u"onomástica/informática/software.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Software móbil", u"Software por tipo"],
                        invalidPagePattern = u"^(Imaxes |Listas |Premio |Navegador web|Videoxogo|{})".format(pattern),
                        validCategoryPattern = u"^({})".format(pattern),
                    ),
                ],
                pageParser = FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/música/acontecementos.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Acontecementos musicais"],
                        validCategoryPattern = u"^(Acontecementos|Festivais|Xiras)",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/organizacións/asociacións.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Asociacións"],
                        invalidPagePattern = u"^(Colectivo|Gremio|Organización non gobernamental)$",
                        validCategoryPattern = u"^(Asociacións|Bandas|Centros|Corais|Entidades|Fundacións|Organizacións|Orquestras|Sindicatos)",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/organizacións/deporte.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Organizacións deportivas"],
                        validCategoryPattern = u"^(Autoridades|Federacións|Organismos|Organizacións)",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/organizacións/economía.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Organizacións económicas"],
                        validCategoryPattern = u"^Organizacións",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/organizacións/internacionais.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Organizacións internacionais"],
                        invalidPagePattern = u"^Organización Internacional$",
                        validCategoryPattern = u"^Organizacións",
                        invalidCategoryAsPagePattern = u"^Personalidades",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/política/partidos.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Partidos políticos"],
                        validCategoryPattern = u"^(Partidos )",
                        invalidPagePattern = u"^(Lista|Partidos) ",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            ),
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Listas de política"],
                        validPagePattern = u"^Partidos inscritos",
                    ),
                ],
                pageParser=TableParser(cellNumbers=[0, 1], skipRows=[0,]),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/televisión/cadeas.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Cadeas de televisión"],
                        validCategoryPattern = u"^(Cadeas|Televisións)",
                        invalidCategoryAsPagePattern = u"^Programas",
                        invalidPagePattern = u"^(Cadea de televisión|Televisión comunitaria)$",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/televisión/debuxos-animados.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Debuxos animados"],
                        validCategoryPattern = u"^(Anime$|Personaxes)",
                        invalidPagePattern = u"^Anime$",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/televisión/grupos.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Grupos de televisión de España"],
                        invalidCategoryPattern = u".",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/baías.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Golfos e baías"],
                        invalidPagePattern = u"^Baía$",
                        validCategoryPattern = u"^Golfos e baías d",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/desertos.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Desertos"],
                        invalidPagePattern = u"^(Desertos d|(Deserto|Serir)$)",
                        validCategoryPattern = u"^Desertos d",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/illas.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryOfPagesNames = [
                            u"Illas e arquipélagos",
                            u"Arquipélagos",
                            u"Atois",
                            u"Illas",
                            u"Illas da Bretaña",
                            u"Illas das Illas Baleares",
                            u"Illas de Asturias",
                            u"Illas de Canarias",
                            u"Illas de Cataluña",
                            u"Illas de Escocia",
                            u"Illas de Galicia",
                            u"Illas deshabitadas",
                            u"Illas ficticias",
                            u"Illas galegas",
                            u"Illas dos Grandes Lagos"
                        ],
                        invalidPagePattern = u"^((Batalla|Lista) |Illa deserta|Illote Motu|Illas de Galicia)",
                        invalidCategoryAsPagePattern = u"^(Illas da baía d.*|Illas do arquipélago d.*|Illas do Xapón|Illas e arquipélagos .*)$",
                        categoryOfCategoriesNames = [u"Illas e arquipélagos por localización", u"Illas por continente", u"Illas por mar", u"Illas por países"],
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/mares.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Mares e océanos"],
                        invalidPagePattern = u"^(Instituto|(Mar|Océano mundial|Zona económica exclusiva)$)",
                        validCategoryPattern = u"^(Mares|Océanos)",
                        invalidCategoryAsPagePattern = u"^(Cidades|Estreitos) ",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/montañas.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Montañas"],
                        validCategoryPattern = u"^(Cordilleiras|Cumes|Montañas|Montes)",
                        invalidPagePattern = u"^(Cumes máis|Lista)",
                        invalidCategoryAsPagePattern = u"^(Imaxes) ",
                    ),
                ],
            ),
            EntryGenerator(
                pageGenerators = [
                    PageLoader(pageNames=[u"Montes de Galicia",]),
                ],
                pageParser=TableParser(cellNumbers=[0, 2], skipRows=[0,]),
                entryParser=EntryParser(separatorsSplitter=[u"/",]),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/penínsulas.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Penínsulas"],
                        validCategoryPattern = u"^Penínsulas (a|d|por |n)",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    pattern = u"(Praias) "
    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/praias.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Praias"],
                        invalidPagePattern = u"^({pattern}|Bandeira Azul$|Galería de imaxes|Praia$|Praia nudista$)".format(pattern=pattern),
                        validCategoryPattern = u"^{pattern}".format(pattern=pattern),
                        invalidCategoryAsPagePattern = u"^(Imaxes) ",
                    ),
                ],
            )
        ],
    ))

    pattern = u"(Rexións) "
    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/rexións.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    PageLoader(
                        [
                            u"Cisxordania",
                            u"Cochinchina",
                            u"Dalmacia",
                            u"Faixa de Gaza",
                        ]
                    ),
                    CategoryBrowser(
                        categoryNames = [u"Rexións de Europa"],
                        invalidPagePattern = u"^({pattern}|Galería de imaxes)".format(pattern=pattern),
                        validCategoryPattern = u"^{pattern}".format(pattern=pattern),
                        invalidCategoryAsPagePattern = u"^(Imaxes) ",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    pattern = u"(Afluentes|Regatos|Ríos) "
    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/accidentes/ríos.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        invalidPagePattern = u"^({pattern}|(Galería de imaxes|Hidrografía|Lista) |(Caneiro \(muíño\)|Pasadoiro|Pontella \(pasaxe\))$)".format(pattern=pattern),
                        validCategoryPattern = u"^{pattern}".format(pattern=pattern),
                        invalidCategoryAsPagePattern = u"^({pattern}|Imaxes)".format(pattern=pattern),
                        categoryOfCategoriesNames = [u"Ríos"],
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaLocalidadesGenerator(u"Desaparecidas", [u"Cidades desaparecidas"])) # Localidades desaparecidas.
    generators.append(GalipediaLocalidadesGenerator(u"Alemaña", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Alxeria"))
    generators.append(GalipediaLocalidadesGenerator(u"Austria", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Bangladesh"))
    generators.append(GalipediaLocalidadesGenerator(u"Barbados"))
    generators.append(GalipediaLocalidadesGenerator(u"Bélxica", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Bolivia"))
    generators.append(GalipediaLocalidadesGenerator(u"Brasil", [u"Cidades do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Burkina Faso", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Cambodja", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Canadá", [u"Cidades do {name}"], pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"China", [u"Cidades da {name}"], pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Colombia", [u"Cidades de {name}", u"Concellos de {name}", u"Correxementos de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Congo", [u"Cidades da República do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Corea do Norte", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Cuba"))
    generators.append(GalipediaLocalidadesGenerator(u"Dinamarca"))
    generators.append(GalipediaLocalidadesGenerator(u"Dominica", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Emiratos Árabes Unidos", [u"Cidades dos {name}"], pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Eslovaquia"))
    generators.append(GalipediaLocalidadesGenerator(u"España", [u"Cidades autónomas de {name}", u"Cidades de {name}", u"Concellos de {name}", u"Parroquias de España"], pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Estados Unidos de América", [u"Cidades dos {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Etiopía"))
    generators.append(GalipediaLocalidadesGenerator(u"Exipto"))
    generators.append(GalipediaLocalidadesGenerator(u"Finlandia", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Francia", [u"Cidades de {name}", u"Concellos de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Grecia", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Grecia antiga", [u"Antigas cidades gregas"]))
    generators.append(GalipediaLocalidadesGenerator(u"Guatemala", [u"Cidades de {name}", u"Municipios de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Guinea-Bisau"))
    generators.append(GalipediaLocalidadesGenerator(u"Hungría"))
    generators.append(GalipediaLocalidadesGenerator(u"Iemen"))
    generators.append(GalipediaLocalidadesGenerator(u"India", [u"Cidades da {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Indonesia"))
    generators.append(GalipediaLocalidadesGenerator(u"Iraq"))
    generators.append(GalipediaLocalidadesGenerator(u"Irlanda"))
    generators.append(GalipediaLocalidadesGenerator(u"Islandia", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Israel"))
    generators.append(GalipediaLocalidadesGenerator(u"Italia", [u"Cidades de {name}", u"Concellos de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Kenya", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Líbano", [u"Cidades do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Malaisia"))
    generators.append(GalipediaLocalidadesGenerator(u"Malí"))
    generators.append(GalipediaLocalidadesGenerator(u"Marrocos", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"México", [u"Cidades de {name}", u"Cidades prehispánicas de {name}", u"Concellos de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Mozambique", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Nepal", [u"Cidades do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Oceanía"))
    generators.append(GalipediaLocalidadesGenerator(u"Omán", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Países Baixos", [u"Cidades dos {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Paquistán"))
    generators.append(GalipediaLocalidadesGenerator(u"Perú", [u"Cidades do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Polonia"))
    generators.append(GalipediaLocalidadesGenerator(u"Portugal", [u"Cidades de {name}", u"Municipios de {name}", u"Vilas de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Qatar"))
    generators.append(GalipediaLocalidadesGenerator(u"Reino Unido", [u"Cidades do {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Romanía"))
    generators.append(GalipediaLocalidadesGenerator(u"Rusia", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Serbia"))
    generators.append(GalipediaLocalidadesGenerator(u"Siria"))
    generators.append(GalipediaLocalidadesGenerator(u"Sudán do Sur", [u"Localidades de {name}"]))
    generators.append(GalipediaLocalidadesGenerator(u"Suecia"))
    generators.append(GalipediaLocalidadesGenerator(u"Suráfrica"))
    generators.append(GalipediaLocalidadesGenerator(u"Suíza"))
    generators.append(GalipediaLocalidadesGenerator(u"Timor Leste"))
    generators.append(GalipediaLocalidadesGenerator(u"Turquía"))
    generators.append(GalipediaLocalidadesGenerator(u"Ucraína", pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Venezuela"))
    generators.append(GalipediaLocalidadesGenerator(u"Xapón", [u"Concellos do {name}"], pageParser=FirstSentenceParser()))
    generators.append(GalipediaLocalidadesGenerator(u"Xordania"))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/lugares/galicia.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Lugares de Galicia", u"Parroquias de Galicia"],
                        invalidPagePattern = u"^(Lugares d|Parroquias d)",
                        validCategoryPattern = u"^(Lugares d|Parroquias d)",
                        invalidCategoryAsPagePattern = u"(^Imaxes d.*|.* sen imaxes$)"
                    ),
                ],
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/países.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [
                            u"Estados desaparecidos",
                            u"Países con recoñecemento limitado",
                            u"Países de América",
                            u"Países de Asia",
                            u"Países de Europa",
                            u"Países de Oceanía",
                            u"Países de África"
                        ],
                        invalidPagePattern = u"^(Concellos |Galería d|Historia d|Lista d|Principais cidades )",
                        validCategoryPattern = u"^(Estados desaparecidos d|Imperios|Países d)",
                        invalidCategoryAsPagePattern = u"^(Capitais d|Emperadores$)",
                    ),
                ],
                pageParser=FirstSentenceParser(),
                entryParser=EntryParser(commaFilter=False),
            )
        ],
    ))

    generators.append(GalipediaRexionsGenerator(u"Alemaña", [u"Estados de {name}", u"Rexións de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Bélxica", [u"Provincias da {name}", u"Rexións de {name}"], pageParser=FirstSentenceParser()))
    generators.append(GalipediaRexionsGenerator(u"Brasil", [u"Estados do {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Chile"))
    generators.append(GalipediaRexionsGenerator(u"Colombia", [u"Departamentos de {name}", u"Provincias de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"España", [u"Comarcas de {name}", u"Comunidades autónomas de {name}", u"Provincias de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Estados Unidos de América", [u"Estados dos {name}", u"Distritos de Nova York"]))
    generators.append(GalipediaRexionsGenerator(u"Finlandia"))
    generators.append(GalipediaRexionsGenerator(u"Francia", [u"Departamentos de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Grecia", [u"Periferias de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Guatemala", [u"Departamentos de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"India", [u"Subdivisións da {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Italia", [u"Rexións de {name}", u"Provincias de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"México", [u"Estados de {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Países Baixos", [u"Provincias dos {name}"]))
    generators.append(GalipediaRexionsGenerator(u"Portugal", [
        u"Antigas provincias de {name}",
        u"Distritos de {name}",
        u"NUTS I portuguesas",
        u"NUTS II portuguesas",
        u"NUTS III portuguesas",
        u"Rexións autónomas de {name}",
    ]))
    generators.append(GalipediaRexionsGenerator(u"Reino Unido", [u"Condados de Inglaterra", u"Condados de Irlanda", u"Divisións de Escocia", u"Rexións de Inglaterra"]))
    generators.append(GalipediaRexionsGenerator(u"Rusia", [u"Repúblicas de {name}"]))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/zonas/españa.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Barrios de España", u"Distritos de España"],
                        invalidPagePattern = u"^(Barrios|Distritos) ",
                        validCategoryPattern = u"^(Barrios|Distritos) "
                    ),
                ],
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/toponimia/zonas/mónaco.dic",
        partOfSpeech = u"topónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Barrios de Mónaco"],
                        invalidPagePattern = u"^Barrios ",
                        validCategoryPattern = u"^Barrios "
                    ),
                ],
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/transporte/aeroportos.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    PageLoader(pageNames=[u"Lista de aeroportos de España",]),
                ],
                pageParser=TableParser(cellNumbers=[4, 5], skipRows=[0,]),
                entryParser=EntryParser(ignoredEntries=[u"?", u"-"]),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/transporte/barcos.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Barcos"],
                        invalidPagePattern = u"^(Babor|Barco|Calado|Desprazamento \(náutica\)|Estribor|Francobordo|Navegación marítima|Popa|Proa|Puntal)$",
                        validCategoryPattern = u"^(Barcos|Embarcacións)",
                        invalidCategoryAsPagePattern = u"^(Accidentes|Imaxes|Tipos)",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/transporte/liñas-aéreas.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Aeroliñas"],
                        invalidPagePattern = u"^(Aeroliña|Aeroliña de baixo custo)$",
                        validCategoryPattern = u"^Aeroliñas",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"onomástica/transporte/trens.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Trens"],
                        validCategoryPattern = u"^Trens",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))


    lineExpression = u"^\* *(\'\'\')? *(\[\[)? *([^][|\']+\|)? *(?P<entry>[^][|\']+) *(\]\])? *(\'\'\')? *:"

    generators.append(GalipediaGenerator(
        resource = u"siglas/campos/alimentación.dic",
        partOfSpeech = u"sigla",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    PageLoader(pageNames = [u"Lista de siglas e acrónimos de alimentación",],),
                ],
                pageParser=LineParser(lineExpression),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"siglas/campos/informática.dic",
        partOfSpeech = u"sigla",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    PageLoader(pageNames = [u"Lista de siglas e acrónimos de informática",],),
                ],
                pageParser=LineParser(lineExpression),
            ),
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Acrónimos de informática"],
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"siglas/campos/medicina.dic",
        partOfSpeech = u"sigla",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    PageLoader(pageNames = [u"Lista de acrónimos en Medicina",],),
                ],
                pageParser=LineParser(lineExpression),
            )
        ],
    ))

    generators.append(GalipediaGenerator(
        resource = u"siglas/xeral.dic",
        partOfSpeech = u"sigla",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    PageLoader(pageNames = [u"Lista de siglas e acrónimos",],),
                ],
                pageParser=LineParser(lineExpression),
            ),
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Acrónimos"],
                        invalidCategoryPattern = u".",
                        invalidCategoryAsPagePattern = u".",
                        invalidPagePattern = u"^(Acrónimo recursivo$|Lista )",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))


    # Wikipedia en castelán.

    generators.append(WikipediaEsGenerator(
        resource = u"antroponimia/xeral.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Nombres por género"],
                        validCategoryPattern = u"^Nombres ",
                        invalidCategoryAsPagePattern = u"^Puranas$",
                    ),
                ],
            )
        ],
    ))

    generators.append(WikipediaEsGenerator(
        resource = u"antroponimia/países/españa.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [
                            u"Ciclistas de la Comunidad de Madrid",
                        ],
                    ),
                ],
            )
        ],
    ))

    generators.append(WikipediaEsGenerator(
        resource = u"antroponimia/países/italia.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [
                            u"Botánicos de Italia del siglo XV",
                            u"Religiosos de Italia del siglo XV",
                            u"Santos de Italia",
                        ],
                        validCategoryPattern = u"^(Cardenales|Obispos|Santos)",
                    ),
                ],
            )
        ],
    ))

    generators.append(WikipediaEsGenerator(
        resource = u"empresas/seguros.dic",
        partOfSpeech = u"nome",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Aseguradoras"],
                        invalidPagePattern = u"^(Compañía de seguros|Reaseguro|Sector asegurador en España)$",
                        validCategoryPattern = u"^(Aseguradoras|Reaseguradoras)",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))


    # Wikipedia en inglés.

    generators.append(WikipediaEnGenerator(
        resource = u"antroponimia/xeral.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Given names by gender"],
                        validCategoryPattern = u".* (god(desse)?s|names)",
                        invalidPagePattern = u"^(Consorts of Ganesha|Forms of Parvati|Ganges in Hinduism|.* Temple)$",
                    ),
                ],
            ),
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Basque given names"],
                        validCategoryPattern = u".* names",
                    ),
                ],
                pageParser=FirstSentenceParser(),
            )
        ],
    ))

    generators.append(WikipediaEnGenerator(
        resource = u"antroponimia/países/brasil.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [
                            u"People by state in Brazil",
                            u"Brazilian mixed martial artists",
                        ],
                        validCategoryPattern = u".*",
                    ),
                ],
            )
        ],
    ))

    generators.append(WikipediaEnGenerator(
        resource = u"antroponimia/países/italia.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Italian sculptors"],
                        validCategoryPattern = u".* (sculptors|stubs)",
                    ),
                ],
            )
        ],
    ))

    generators.append(WikipediaEnGenerator(
        resource = u"antroponimia/países/méxico.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"People from Oaxaca"],
                        validCategoryPattern = u"^(Members|Musicians|People|Singers) ",
                    ),
                ],
            )
        ],
    ))

    generators.append(WikipediaEnGenerator(
        resource = u"antroponimia/países/países-baixos.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Dutch footballers"],
                        invalidPagePattern = u"^List of",
                        validCategoryPattern = u".*(footballers|stubs)",
                    ),
                ],
            )
        ],
    ))

    generators.append(WikipediaEnGenerator(
        resource = u"antroponimia/países/rusia.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"People from Bryansk"],
                    ),
                ],
            )
        ],
    ))

    # Wikipedia en húngaro.

    generators.append(WikipediaHuGenerator(
        resource = u"antroponimia.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryOfCategoriesNames = [u"Férfikeresztnevek", u"Női keresztnevek"],
                    ),
                ],
            )
        ],
    ))

    # Wikipedia en portugués.

    generators.append(WikipediaPtGenerator(
        resource = u"antroponimia/países/brasil.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Atores do Brasil",],
                        invalidPagePattern = u"^(Anexo:|Vedete$)",
                        validCategoryPattern = u"^(Atores|Estrelas|Vedetes)",
                        invalidCategoryAsPagePattern = u"^(!|Imagens)",
                    ),
                ],
            )
        ],
    ))

    generators.append(WikipediaPtGenerator(
        resource = u"antroponimia/países/españa.dic",
        partOfSpeech = u"antropónimo",
        entryGenerators=[
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Reis de Leão",],
                        invalidPagePattern = u"^Anexo:",
                    ),
                ],
            )
        ],
    ))


    return generators