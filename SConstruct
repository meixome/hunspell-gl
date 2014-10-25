# coding=utf-8

import mmap, os, PyICU, re, subprocess

#---# Valores predeterminados #----------------------------------------------------------------------------------------#

defaultAff  = u'norma'
defaultDic  = u'drag,norma'
defaultRep  = u'comunidade,drag,wikipedia'
defaultCode = u'gl'

#---# Axuda #----------------------------------------------------------------------------------------------------------#

Help("""
Execute:

    «scons aff=<módulos de regras> dic=<módulos de vocabulario> rep=<módulos de substitucións> code=<código de lingua>»

Esta orde permite construír o corrector cos módulos indicados para cada unha das categorías (regras de construción de
palabras, listas de núcleos de palabras e regras de substitución), empregando o código de lingua indicado para o
nome dos ficheiros.

Para combinar varios módulos, sepáreos con comas (sen espazos). Por exemplo:

    scons dic=drag,norma

Para incluír submódulos, sepáreos do módulo pai cunha barra inclinada. Por exemplo, para incluír o vocabulario do
submódulo «onomástica» do módulo «wikipedia», use:

    scons dic=wikipedia/onomástica

Os valores por omisión son:

    Regras: {aff}.
    Dicionario: {dic}.
    Substitucións: {rep}.
    Código de lingua: {code} (dá lugar a «{code}.aff» e «{code}.dic»).

En «módulos.txt» atopará unha lista de módulos dispoñíbeis.
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
    """ Constrúe o ficheiro .aff base a partir dos módulos indicados.
    """
    baseFilesCount = len(sourceFilenames)
    if baseFilesCount > 1:
        print u"O corrector só pode constar dun único ficheiro «.base»."
        raise Exception()
    elif baseFilesCount < 1:
        print u"O corrector debe incluír un ficheiro «.base»."
        print u"Inclúa un módulo con ficheiro de regras base (por exemplo, «norma») na lista de ficheiros do parámetro «aff»."
        raise Exception()

    initialize(targetFilename)
    for sourceFilename in sourceFilenames:
        parsedContent = getParsedContent(sourceFilename)
        extendAffFromString(targetFilename, parsedContent)


def addContentToAff(targetFilename, sourceFilenames):
    """ Amplía o ficheiro .aff base a partir dos módulos indicados.
    """
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

    if linesSeen:

        formattedContentWithoutDuplicates = "REP {count}\n".format(count=len(linesSeen))
        collator = PyICU.Collator.createInstance(PyICU.Locale('gl.UTF-8'))
        for line in sorted(linesSeen, cmp=collator.compare):
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
    collator = PyICU.Collator.createInstance(PyICU.Locale('gl.UTF-8'))
    for line in sorted(linesSeen, cmp=collator.compare):
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
            if filename.endswith(extension):
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
    sourceFiles.extend(getSourceFilesFromModulesStringAndExtension(rules, '.base'))
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
        for extension in extensionList:
            if filename.endswith(extension):
                filenames.append(filename)
    return filenames


def createSpellchecker(target, source, env):
    aff = unicode(target[0])
    dic = unicode(target[1])
    createAff(aff, getFilenamesFromFileEntriesWithMatchingExtensions(source, ['.base']))
    addContentToAff(aff, getFilenamesFromFileEntriesWithMatchingExtensions(source, ['.aff']))
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

