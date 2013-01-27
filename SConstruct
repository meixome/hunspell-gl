# coding=utf-8

import mmap, os

#---# Valores predeterminados #----------------------------------------------------------------------------------------#

defaultAff  = u'norma,unidades'
defaultDic  = u'iso639,unidades,volga'
defaultCode = u'gl'

#---# Axuda #----------------------------------------------------------------------------------------------------------#

Help("""
Execute «scons aff=<módulos de regras> dic=<módulos de dicionario> code=<código de lingua>» para construír o corrector cos módulos indicados para as regras e o dicionario, empregando o código de lingua indicado para o nome dos ficheiros.

Para combinar varios módulos, sepáreos con comas (sen espazos). Por exemplo:

    scons dic=volga,unidades

Os valores por omisión son:

    Regras: {aff}.
    Dicionario: {dic}.
    Código de lingua: {code} (dá lugar a «{code}.aff» e «{code}.dic»).

Módulos dispoñíbeis:


    REGRAS

    norma           Normas ortográficas e morfolóxicas do idioma galego
                    Real Academia Galega / Instituto da Lingua Galega, 2003.
                    http://www.realacademiagalega.org/PlainRAG/catalog/publications/files/normas_galego05.pdf
            
    unidades        Prefixos e sufixos para símbolos de unidades.
                    http://en.wikipedia.org/wiki/International_System_of_Units
                    Nota: inclúense prefixos para unidades binarias.


    DICIONARIO
            
    iso639          Códigos de linguas (ISO 639).
                    http://en.wikipedia.org/wiki/ISO_639
            
    unidades        Símbolos de unidades.
                    http://en.wikipedia.org/wiki/International_System_of_Units
                    Nota: inclúense unidades de fóra do S.I., como byte (B) ou quintal métrico (q) ou tonelada (t).

    volga           Vocabulario ortográfico da lingua galega
                    Santamarina Fernández, Antón e González González, Manuel (coord.)
                    Real Academia Galega / Instituto da Lingua Galega, 2004.
                    http://www.realacademiagalega.org/volga/
    
""".format(aff=defaultAff, dic=defaultDic, code=defaultCode))


#---# Builders #-------------------------------------------------------------------------------------------------------#


def initialize(target):
    """ Crea un ficheiro baleiro na ruta indicada.
    """
    with open(target, 'w') as file:
        file.write('')


def isModule(directory):
    """ Determina se o directorio indicado é un módulo.
    """
    if unicode(directory) == 'src':
        return False
    else:
        return True


def extendHeader(target, source, env):
    """ Inclúe os datos para a cabeceira do módulo de orixe no ficheiro de destino.
    """
    with open(target, 'a') as targetFile:
        try:
            with open(os.path.join(source, 'header.txt')) as sourceFile:
                targetFile.write(sourceFile.read())
        except IOError:
            pass


def extendAff(target, source, env):
    """ Inclúe datos do módulo de orixe nun ficheiro .aff, o de destino, que pode que exista ou que non.
    """
    with open(target, 'a') as targetFile:
        try:
            with open(os.path.join(source, 'main.aff')) as sourceFile:
                targetFile.write(sourceFile.read())
        except IOError:
            pass


def extendDic(target, source):
    """ Inclúe datos do módulo de orixe nun ficheiro .dic, o de destino, que pode que exista ou que non.
    """
    try:
        with open(os.path.join(source, 'main.dic')) as sourceFile:
            return sourceFile.read()
    except IOError:
        return ''


def createAff(target, source, env):
    """ Constrúe o ficheiro .aff a partir dos módulos indicados.
    """
    target = unicode(target[0])
    initialize(target)
    for directory in source:
        if isModule(directory):
            extendHeader(target, unicode(directory), env)
    for directory in source:
        if isModule(directory):
            extendAff(target, unicode(directory), env)


def createDic(target, source, env):
    """ Constrúe o ficheiro .dic a partir dos módulos indicados.
    """
    target = unicode(target[0])
    content = ''
    for directory in source:
        if isModule(directory):
            content += extendDic(target, unicode(directory))
    contentLines = content.count('\n')
    with open(target, 'w') as targetFile:
        targetFile.write('{}\n{}'.format(contentLines, content))
        
        
def parseModuleList(string):
    if ',' in string:
        return [Dir('src/{}'.format(module)) for module in string.split(',')]
    else:
        return [Dir('src/{}'.format(string))]


# Construtores para os ficheiros de Hunspell.
env = Environment()
env['BUILDERS']['rules'] = Builder(action = createAff)
env['BUILDERS']['dictionary'] = Builder(action = createDic)


#---# Análise dos argumentos da chamada #------------------------------------------------------------------------------#

languageCode = ARGUMENTS.get('code', defaultCode)
rules = ARGUMENTS.get('aff', defaultAff)
dictionary = ARGUMENTS.get('dic', defaultDic)


#---# Construción #----------------------------------------------------------------------------------------------------#

env.rules('build/{}.aff'.format(languageCode), parseModuleList(rules))
env.dictionary('build/{}.dic'.format(languageCode), parseModuleList(dictionary))
