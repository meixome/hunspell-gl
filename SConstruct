# coding=utf-8

import mmap, os

#---# HELP #-----------------------------------------------------------------------------------------------------------#

Help("""
Type: 'scons [aff=<rules>] [dic=<dictionary name>] [lang=<language code>]' to build the spellchecker with the specified
rules and dictionary, using the specified language code for the filename.

Supported values:


    RULES

    core    Normas ortográficas e morfolóxicas do idioma galego
            Real Academia Galega / Instituto da Lingua Galega, 2003.
            http://www.realacademiagalega.org/PlainRAG/catalog/publications/files/normas_galego05.pdf


    DICTIONARY

    volga   Vocabulario ortográfico da lingua galega
            Santamarina Fernández, Antón e González González, Manuel (coord.)
            Real Academia Galega / Instituto da Lingua Galega, 2004.
            http://www.realacademiagalega.org/volga/


Default values are ‘core’ for the rules and ‘volga’ for the dictionary. Default language code is ‘gl’, resulting in the
files ‘gl.aff’ and ‘gl.dic’.


You can optionally define the rules or dictionary specifying a comma-separated list of modules. Example:

    scons dic=volga,trasno,numbers,names
    
To specify a single module, add a comma to it as suffix:

    scons dic=trasno,
    
Supported modules are:

    core    Normas ortográficas e morfolóxicas do idioma galego
            Real Academia Galega / Instituto da Lingua Galega, 2003.
            http://www.realacademiagalega.org/PlainRAG/catalog/publications/files/normas_galego05.pdf
    
    volga   Vocabulario ortográfico da lingua galega
            Santamarina Fernández, Antón e González González, Manuel (coord.)
            Real Academia Galega / Instituto da Lingua Galega, 2004.
            http://www.realacademiagalega.org/volga/
    
""")


#---# Builders #-------------------------------------------------------------------------------------------------------#


# Creates an empty file at the specified location.
#
def initialize(target):
    with open(target, 'w') as file:
        file.write('')


# Determines whether the specified directory is a module.
#
def isModule(directory):
    if unicode(directory) == 'src':
        return False
    else:
        return True


# Includes header data from the source module in the target file.
#
# To be called from extendAff() and extendDic().
#
def extendHeader(target, source, env):
    with open(target, 'a') as targetFile:
        try:
            with open(os.path.join(source, 'header.txt')) as sourceFile:
                targetFile.write(sourceFile.read())
        except IOError:
            pass


# Includes data from the source module in an existing or non-existing .aff file (the target).
#
# To be called from createAff().
#
def extendAff(target, source, env):
    with open(target, 'a') as targetFile:
        try:
            with open(os.path.join(source, 'main.aff')) as sourceFile:
                targetFile.write(sourceFile.read())
        except IOError:
            pass


# Includes data from the source module in an existing or non-existing .dic file (the target).
#
# To be called from createDic().
#
def extendDic(target, source):
        try:
            with open(os.path.join(source, 'main.dic')) as sourceFile:
                return sourceFile.read()
        except IOError:
            return ''


# Builds the target .aff file from the specified source modules.
#
def createAff(target, source, env):
    target = unicode(target[0])
    initialize(target)
    for directory in source:
        if isModule(directory):
            extendHeader(target, unicode(directory), env)
    for directory in source:
        if isModule(directory):
            extendAff(target, unicode(directory), env)


# Builds the target .dic file from the specified source modules.
#
def createDic(target, source, env):
    target = unicode(target[0])
    content = ''
    for directory in source:
        if isModule(directory):
            content += extendDic(target, unicode(directory))
    contentLines = content.count('\n')
    with open(target, 'w') as targetFile:
        targetFile.write('{}\n{}'.format(contentLines, content))


# Hunspell file builder.
env = Environment()
env['BUILDERS']['rules'] = Builder(action = createAff)
env['BUILDERS']['dictionary'] = Builder(action = createDic)


#---# ARGUMENTS PARSING #----------------------------------------------------------------------------------------------#

languageCode = ARGUMENTS.get('code', 'gl')
rules = ARGUMENTS.get('aff', 'core')
dictionary = ARGUMENTS.get('dic', 'volga')


#---# BUILD #----------------------------------------------------------------------------------------------------------#




# RULES (.aff)
if ',' in rules:
    env.rules('build/{}.aff'.format(languageCode), [Dir('src/{}'.format(module)) for module in rules.split(',')])
elif rules == 'core':
    env.rules('build/{}.aff'.format(languageCode), [Dir('src/{}'.format(module)) for module in ['core']])
else:
    raise Exception('Unsuported rules: {}'.format(rules))


# DICTIONARY (.dic)

if ',' in dictionary:
    env.dictionary('build/{}.dic'.format(languageCode), [Dir('src/{}'.format(module)) for module in dictionary.split(',')])
elif dictionary == 'volga':
    env.dictionary('build/{}.dic'.format(languageCode), [Dir('src/{}'.format(module)) for module in ['core', 'volga']])
elif dictionary == 'trasno':
    env.dictionary('build/{}.dic'.format(languageCode), [Dir('src/{}'.format(module)) for module in ['core', 'volga', 'trasno']])
else:
    raise Exception('Unsuported dictionary: {}'.format(dictionary))    
