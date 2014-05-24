# -*- coding:utf-8 -*-

import os, re, subprocess, sys

import common, test



unescapedSlash = re.compile(u"error: line (\d+): 0 is wrong flag id")
multipleDefinitions = re.compile(u"error: line (\d+): multiple definitions of an affix flag")



def check(path):

    errors = 0

    args = [
        u"hunspell",
        u"-d",
        path,
        u"-l",
    ]
    hunspell = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    standardOutput, errorOutput = hunspell.communicate(u"proba")
    for line in errorOutput.splitlines():

        errors += 1

        match = unescapedSlash.match(line)
        if match:
            lineNumber = int(match.group(1))
            lineContent = common.getLineFromFile(path + u".dic", lineNumber)
            common.error(u"Hai unha barra inclinada («/») sen escapar na liña {} do dicionario («{}»).".format(lineNumber, lineContent))
            continue

        match = multipleDefinitions.match(line)
        if match:
            lineNumber = int(match.group(1))
            lineContent = common.getLineFromFile(path + u".dic", lineNumber)
            common.error(u"Definición duplicada de marca na liña {} do dicionario («{}»).".format(lineNumber, lineContent))
            continue

        common.error(u"O executábel de Hunspell informou do seguinte erro: «{}».".format(line))

    return errors



class SyntaxTest(test.Test):

    def __init__(self):

        super(SyntaxTest, self).__init__()

        self.path = "sintaxe"


    def getAllModules(self):
        modules = []
        rootPath, folderNames, fileNames = next(os.walk(common.getSourcePath()))
        for folderName in folderNames:
            modules.append(folderName)
        for fileName in fileNames:
            modules.append(fileName)
        return modules


    def run(self, spellCheckerManager):
        modules = self.getAllModules()
        config = {
            "aff": modules,
            "dic": modules,
            "rep": modules,
        }
        self.spellCheckerPath = spellCheckerManager.create(config)
        self.errors += check(self.spellCheckerPath)
        self.report()



def loadTestList():
    return [SyntaxTest(),]