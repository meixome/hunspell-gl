# coding=utf-8

import mmap, os, re, subprocess

#---# Valores predeterminados #----------------------------------------------------------------------------------------#

defaultAff  = u'norma,unidades'
defaultDic  = u'comunidade,iso639,iso4217,unidades,volga'
defaultRep  = u'comunidade,galipedia'
defaultCode = u'gl'

#---# Axuda #----------------------------------------------------------------------------------------------------------#

Help("""
Execute:

    «scons aff=<módulos de regras> dic=<módulos de vocabulario> rep=<módulos de substitucións> code=<código de lingua>»

Esta orde permite construír o corrector cos módulos indicados para cada unha das categorías (regras de construción de
palabras, listas de núcleos de palabras e regras de substitución), empregando o código de lingua indicado para o
nome dos ficheiros.

Para combinar varios módulos, sepáreos con comas (sen espazos). Por exemplo:

    scons dic=volga,unidades

Para incluír submódulos, sepáreos do módulo pai cunha barra inclinada. Por exemplo, para incluír o vocabulario do
submódulo «toponimia» do módulo «galipedia», use:

    scons dic=galipedia/toponimia

Os valores por omisión son:

    Regras: {aff}.
    Dicionario: {dic}.
    Substitucións: {rep}.
    Código de lingua: {code} (dá lugar a «{code}.aff» e «{code}.dic»).

Módulos dispoñíbeis:


    FAMILIAS DE REGRAS DE CONSTRUCIÓN DE PALABRAS

    norma           Normas ortográficas e morfolóxicas do idioma galego
                    Real Academia Galega / Instituto da Lingua Galega, 2003
                    http://www.realacademiagalega.org/PlainRAG/catalog/publications/files/normas_galego05.pdf

    trasno          Flexións especiais para os acordos terminolóxicos do Proxecto Trasno
                    http://trasno.net/content/resultados-das-trasnadas

    unidades        Prefixos e sufixos para símbolos de unidades
                    http://en.wikipedia.org/wiki/International_System_of_Units
                    Nota: inclúense prefixos para unidades binarias.


    DICIONARIOS DE NÚCLEOS DE PALABRAS
    
    comunidade      Vocabulario da comunidade do corrector de galego Hunspell
                    Termos engadidos ao corrector sen indicar unha fonte que os apoie.
                    Nota: trátase de vocabulario que debe revisarse e repartirse entre os outros módulos.
                    
    galipedia       Galipedia
                    http://gl.wikipedia.org/wiki/Portada
                    
                    Submódulos:
                        
                    • toponimia. Topónimos.
                        • accidentes. Nomes de accidentes xeográficos.
                            • continentes
                            • illas
                            • montañas
                        • localidades. Nomes de núcleos de poboación: cidades, comunas, concellos, vilas…
                            • alxeria
                            • españa
                            • estados-unidos-de-américa
                            • etiopía
                            • exipto
                            • francia
                            • grecia
                            • iemen
                            • indonesia
                            • iraq
                            • israel
                            • italia
                            • líbano
                            • malí
                            • méxico
                            • oceanía
                            • países-baixos
                            • perú
                            • portugal
                            • reino-unido
                            • suíza
                            • turquía
                            • xordania
                        • lugares. Nomes de lugares e parroquias.
                            • galicia. Véxase: http://gl.wikipedia.org/wiki/Categoría:Lugares_de_Galicia
                        • países. Nomes de países do mundo, actuais e pasados, de recoñecemento amplo ou limitado.
                        • rexións. Topónimos entre localidades e estados: comunidades, condados, provincias, rexións…
                            • brasil
                            • chile
                            • colombia
                            • españa
                            • estados-unidos-de-américa
                            • francia
                            • italia
                            • portugal
                        • zonas. Nomes de barrios e distritos.
                            • españa
                    • xeografía. Xeografía.
                        • accidentes. Accidentes xeográficos.

    iso639          Códigos de linguas (ISO 639)
                    http://gl.wikipedia.org/wiki/ISO_639

    iso4217         Códigos de moedas (ISO 4217)
                    http://gl.wikipedia.org/wiki/ISO_4217

    trasno          Acordos terminolóxicos do Proxecto Trasno
                    http://trasno.net/content/resultados-das-trasnadas

    unidades        Símbolos de unidades
                    http://en.wikipedia.org/wiki/International_System_of_Units
                    Nota: inclúense unidades de fóra do S.I., como byte (B) ou quintal métrico (q) ou tonelada (t).

    volga           Vocabulario ortográfico da lingua galega
                    Santamarina Fernández, Antón e González González, Manuel (coord.)
                    Real Academia Galega / Instituto da Lingua Galega, 2004
                    http://www.realacademiagalega.org/volga/
                    
                    Submódulos:
                        
                    • correcto. Vocabulario correcto.
                    • tolerado. Vocabulario tolerado.


    REGRAS DE SUXESTIÓNS DE SUBSTITUCIÓN DE PALABRAS INCORRECTAS POR PALABRAS CORRECTAS
    
    comunidade      Suxestións da comunidade do corrector de galego Hunspell
                    Suxestións engadidas ao corrector sen indicar unha fonte que as apoie.
                    Nota: trátase de suxestións que deben revisarse e repartirse entre os outros módulos.

    galipedia       Erros ortográficos e desviacións máis comúns rexistrados na Galipedia
                    http://gl.wikipedia.org/wiki/Wikipedia:Erros_de_ortografía_e_desviacións


""".format(aff=defaultAff, dic=defaultDic, rep=defaultRep, code=defaultCode))


#---# Builders #-------------------------------------------------------------------------------------------------------#


def initialize(target):
    """ Crea un ficheiro baleiro na ruta indicada.
    """
    with open(target, 'w') as file:
        file.write('')


def isNotUseless(line):
    """ Determina se a liña indicada ten algunha utilidade para o corrector, ou se pola contra se trata dunha liña que
        ten unicamente un comentario, ou se trata duña liña baleira.
    """
    strippedLine = line.strip()
    if strippedLine == "":
        return False
    elif strippedLine[0] == "#":
        return False
    else:
        return True


def removeAnyCommentFrom(line):
    """ Se a liña ten un comentario, elimínao.

        Nota: se a liña acababa en salto de liña, este tamén se eliminará xunto co comentario.
    """
    index = line.find('#')
    if index < 0:
        return line
    else:
        return line[0:index]


def removeMultipleSpacesOrTabsFrom(line):
    """ Converte as tabulacións da liña en espazos, e reduce estes ao mínimo necesario. É dicir, toda tabulación ou
        grupo de tabulacións e grupo de espazos quedarán reducidos a un único espazo cada un.

        Por exemplo, se a liña é:

            "\t\t\t1\tasdfasdf    2  \t\t  \t 3"

        Devolverase:

            " 1 2 3"
    """
    line = line.replace('\t', ' ')
    line = re.sub(' +', ' ', line)
    return line



def stripLine(line):
    line = removeAnyCommentFrom(line)
    line = line.rstrip() + '\n'
    line = removeMultipleSpacesOrTabsFrom(line)
    return line


def extendAffFromString(targetFilename, sourceString):
    """ Inclúe datos do módulo de orixe, fornecidos mediante unha cadea de texto, nun ficheiro .aff.
    """
    with open(targetFilename, 'a') as targetFile:
        try:
            targetFile.write(sourceString)
        except IOError:
            pass


def createAff(targetFilename, sourceFilenames):
    """ Constrúe o ficheiro .aff a partir dos módulos indicados.
    """
    initialize(targetFilename)
    for sourceFilename in sourceFilenames:
        parsedContent = getParsedContent(sourceFilename)
        extendAffFromString(targetFilename, parsedContent)


def addReplacementsToAff(targetFilename, sourceFilenames):
    """ Completa o ficheiro .aff a partir dos ficheiros de substitucións dos módulos indicados.
    """
    content = ''
    for sourceFilename in sourceFilenames:
        content += getParsedContent(sourceFilename)

    linesSeen = set()
    for line in iter(content.splitlines()):
        if line not in linesSeen:
            linesSeen.add(line)

    formattedContentWithoutDuplicates = "REP {count}\n".format(count=len(linesSeen))
    for line in sorted(linesSeen):
        formattedContentWithoutDuplicates += "REP {replacement}\n".format(replacement=line)
    
    extendAffFromString(targetFilename, formattedContentWithoutDuplicates)


def getParsedContent(sourceFilename):
    """ Inclúe datos do módulo de orixe nun ficheiro .dic, o de destino, que pode que exista ou que non.
    """
    try:
        parsedContent = ""
        with open(sourceFilename) as sourceFile:
            for line in sourceFile:
                if isNotUseless(line):
                    parsedContent += stripLine(line)
        return parsedContent
    except IOError:
        return ''


def createDic(targetFilename, sourceFilenames):
    """ Constrúe o ficheiro .dic a partir dos módulos indicados.
    """
    content = ''
    for sourceFilename in sourceFilenames:
        content += getParsedContent(sourceFilename)

    linesSeen = set()
    for line in iter(content.splitlines()):
        if line not in linesSeen:
            linesSeen.add(line)

    contentWithoutDuplicates = ""
    for line in sorted(linesSeen):
        contentWithoutDuplicates += line + '\n'

    with open(targetFilename, 'w') as targetFile:
        targetFile.write('{}\n{}'.format(len(linesSeen), contentWithoutDuplicates))


def getAliasFilepathFor(filepath):
    return filepath[:-4] + '_alias' + filepath[-4:]


def applyMakealias(aff, dic):
    """ Executa a orde «makealias», de Hunspell, para reducir o tamaño final dos ficheiros considerablemente.
    
            Nota: Desactivado de maneira temporal. Véxase:
            
                http://sourceforge.net/tracker/?func=detail&aid=3610768&group_id=143754&atid=756395
    """
    #affAlias = getAliasFilepathFor(aff)
    #dicAlias = getAliasFilepathFor(dic)
    #command = 'makealias {dic} {aff}'.format(aff=aff[6:], dic=dic[6:])
    #p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, cwd=os.path.join(os.getcwd(), 'build'))
    #out, err = p.communicate()
    #for filepath in [aff, dic]:
        #os.remove(filepath)
        #os.rename(getAliasFilepathFor(filepath), filepath)


def getModuleListFromModulesString(modulesString):
    modules = []
    if ',' in modulesString:
        modules = ['src/{}'.format(module) for module in modulesString.split(',')]
    else:
        modules = ['src/{}'.format(modulesString)]
    return modules


def getSourceFilesFromFolderAndExtension(folder, extension):

    sourceFiles = []

    for dirname, dirnames, filenames in os.walk(folder):
        for filename in filenames:
            if filename[-len(extension):] == extension:
                sourceFiles.append(os.path.join(dirname, filename))

    return sourceFiles


def getSourceFilesFromModulesStringAndExtension(modulesString, extension):

    sourceFiles = []

    modules = getModuleListFromModulesString(modulesString)
    for module in modules:

        # If module is a folder, get all .<extension> files inside.
        if os.path.isdir(module):
            for filepath in getSourceFilesFromFolderAndExtension(module, extension):
                sourceFiles.append(File(filepath))

        # If with .<extension> it is a file, include the file.
        # Note: if both a <module> folder and a <module>.<extension> file exist, both are added.
        filepath = '{module}{extension}'.format(module=module, extension=extension)
        if os.path.isfile(filepath):
            sourceFiles.append(File(filepath))

    return sourceFiles


def getSourceFiles(dictionary, rules, replacements):
    sourceFiles = []
    sourceFiles.extend(getSourceFilesFromModulesStringAndExtension(rules, '.aff'))
    sourceFiles.extend(getSourceFilesFromModulesStringAndExtension(dictionary, '.dic'))
    sourceFiles.extend(getSourceFilesFromModulesStringAndExtension(replacements, '.rep'))
    return sourceFiles


def getFilenamesFromFileEntriesWithMatchingExtensions(fileEntries, extensionList):
    """ Note: Only supports three-letter extensions. For example: '.aff', '.dic', '.rep'.
    """
    filenames = []
    for fileEntry in fileEntries:
        filename = str(fileEntry)
        if filename[-4:] in extensionList:
            filenames.append(filename)
    return filenames


def createSpellchecker(target, source, env):
    aff = unicode(target[0])
    dic = unicode(target[1])
    createAff(aff, getFilenamesFromFileEntriesWithMatchingExtensions(source, ['.aff']))
    addReplacementsToAff(aff, getFilenamesFromFileEntriesWithMatchingExtensions(source, ['.rep']))
    createDic(dic, getFilenamesFromFileEntriesWithMatchingExtensions(source, ['.dic']))
    applyMakealias(aff, dic)


#---# Análise dos argumentos da chamada #------------------------------------------------------------------------------#

languageCode = ARGUMENTS.get('code', defaultCode)
rules = ARGUMENTS.get('aff', defaultAff)
dictionary = ARGUMENTS.get('dic', defaultDic)
replacements = ARGUMENTS.get('rep', defaultRep)


# Construtor para os ficheiros de Hunspell.
env = Environment()
env['BUILDERS']['spellchecker'] = Builder(action = createSpellchecker)


#---# Construción #----------------------------------------------------------------------------------------------------#

env.spellchecker(
    ['build/{}.aff'.format(languageCode), 'build/{}.dic'.format(languageCode)],
    getSourceFiles(dictionary=dictionary, rules=rules, replacements=replacements)
)

