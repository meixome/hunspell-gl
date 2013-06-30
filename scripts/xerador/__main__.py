# -*- coding:utf-8 -*-

import os, sys
import common, galipedia, iso


def getFirstPathRelativeToSecondPathIfWithin(childPath, parentPath):
    absoluteChildPath = os.path.abspath(childPath)
    absoluteParentPath = os.path.abspath(parentPath)
    if (absoluteChildPath.startswith(absoluteParentPath)):
        childPath = absoluteChildPath[len(absoluteParentPath)+1:]
    return childPath


def loadGeneratorList():
    generators = []
    generators.extend(galipedia.loadGeneratorList())
    generators.extend(iso.loadGeneratorList())
    return generators


# Program starts.

modulesSourcePath = common.getModulesSourcePath()
generators = loadGeneratorList()

for parameter in [parameter.decode('UTF-8') for parameter in sys.argv[1:]]:
    modulePath = getFirstPathRelativeToSecondPathIfWithin(parameter, modulesSourcePath)
    usedGenerators = 0
    for generator in generators:
        if generator.resource.startswith(modulePath):
            print u":: Actualizando {resource}…".format(resource=generator.resource)
            generator.run()
            usedGenerators += 1
    if usedGenerators == 0:
        print u"Non existe ningún xerador para o módulo «{module}».".format(module=modulePath)