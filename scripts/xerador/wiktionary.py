# -*- coding:utf-8 -*-

from mediawiki import MediaWikiGenerator  # Dictionary generators.
from mediawiki import EntryGenerator  # Entry generators.
from mediawiki import PageLoader, CategoryBrowser  # Page generators.
from mediawiki import TitleParser, FirstSentenceParser, LineParser, TableParser  # Page parsers.
from mediawiki import EntryParser  # Page parsers.



class WiktionaryGenerator(MediaWikiGenerator):

    def __init__(self, languageCode, resource, partOfSpeech, entryGenerators):
        super(WiktionaryGenerator, self).__init__(
                siteName=u"wiktionary",
                languageCode=languageCode,
                resource=resource,
                partOfSpeech=partOfSpeech,
                entryGenerators=entryGenerators,
            )


class GalizionarioGenerator(WiktionaryGenerator):

    def __init__(self, resource, partOfSpeech, entryGenerators):
        super(GalizionarioGenerator, self).__init__(
                "gl",
                resource,
                partOfSpeech,
                entryGenerators=entryGenerators,
            )




class GalizionarioNamesGenerator(GalizionarioGenerator):

    def __init__(self):

        pageNames = [u"Apéndice:Nomes de persoa",]
        pageLoader = PageLoader(pageNames=pageNames)

        tableParser = TableParser(cellNumbers=[0, 3, 4])

        super(GalizionarioNamesGenerator, self).__init__(
            resource = u"antroponimia.dic",
            partOfSpeech = u"antropónimo",
            entryGenerators = [
                EntryGenerator(
                    pageGenerators=[pageLoader,],
                    pageParser=tableParser,
                    entryParser=EntryParser(
                        commaSplitter=True,
                        commaFilter=False,
                        semicolonSplitter=True,
                    )
                ),
            ]
        )



class WiktionaryEnGenerator(WiktionaryGenerator):

    def __init__(self, resource, partOfSpeech, entryGenerators):
        super(WiktionaryEnGenerator, self).__init__(
                "en",
                resource,
                partOfSpeech,
                entryGenerators=entryGenerators,
            )


class WiktionaryEnNamesGenerator(WiktionaryEnGenerator):

    def __init__(self):

        import string

        pageNames = set()
        for pagePrefix in [u"Appendix:Female given names/", u"Appendix:Male given names/"]:
            for letter in list(string.ascii_uppercase):
                pageNames.add(pagePrefix + letter)
        pageLoader = PageLoader(pageNames=pageNames)

        namePattern = u"^: *(\'\'\')? *\[\[ *([^]|]+\|)? *(?P<entry>[^]|]+) *\]\]"
        ignorePattern = u"^-"
        lineParser = LineParser(namePattern, ignorePattern=ignorePattern)

        super(WiktionaryEnNamesGenerator, self).__init__(
                "antroponimia.dic",
                u"antropónimo",
                [
                    EntryGenerator(
                        pageGenerators=[pageLoader,],
                        pageParser=lineParser,
                    ),
                ]
            )



def loadGeneratorList():

    generators = []


    # Galizionario.

    generators.append(GalizionarioNamesGenerator())

    generators.append(GalizionarioGenerator(
        resource = u"toponimia/xeral.dic",
        partOfSpeech = u"topónimo",
        entryGenerators= [
            EntryGenerator(
                pageGenerators = [
                    CategoryBrowser(
                        categoryNames = [u"Toponimia en galego"],
                        ignoreCategoryNames = [u"Toponimia de Galicia en galego"]
                    ),
                ],
            ),
        ]
    ))

    generators.append(GalizionarioGenerator(
        u"toponimia/galicia.dic",
        u"topónimo",
        entryGenerators= [
            EntryGenerator(
                pageGenerators=[
                    CategoryBrowser(
                        categoryNames = [u"Toponimia de Galicia en galego"]
                    ),
                ]
            )
        ]
    ))


    # Wiktionary en inglés.

    generators.append(WiktionaryEnNamesGenerator())


    # TODO: Desenvolver un sistema de determinación das liñas correctas de feminino e plural para o Hunspell.
    # Por exemplo: «capixaba/10» para «capixaba/s».
    #generators.append(GalizionarioGenerator(
        #resource = u"xentilicio/xeral.dic",
        #partOfSpeech = u"xentilicio",
        #categoryNames = [u"Xentilicio en galego"]
    #))

    return generators
