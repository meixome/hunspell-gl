# -*- coding:utf-8 -*-

import codecs, os, shutil, subprocess, sys

import common, spellchecker, syntax, test



class SpellingTest(test.Test):

    def __init__(self, path):

        super(SpellingTest, self).__init__()

        self.path = path
        self._config = None

        self.spellCheckerPath = None
        self.spellCheckerManager = None


    def config(self):
        if self._config is None:
            import json
            try:
                with codecs.open(os.path.join(common.getTestsPath(), self.path + u".json"), "r", "utf-8") as fileObject:
                    self._config = json.load(fileObject)
            except ValueError:
                self._config = {}
            defaultModules = ["rag/gl", "norma"]
            if "aff" not in self._config: self._config["aff"] = defaultModules
            if "dic" not in self._config: self._config["dic"] = defaultModules
            if "rep" not in self._config: self._config["rep"] = defaultModules
        return self._config


    def generateSpellChecker(self):
        config = self.config()
        self.spellCheckerPath = self.spellCheckerManager.create(config)
        self.errors += syntax.check(self.spellCheckerPath)


    def iterFileLines(self, path):
        if os.path.exists(path):
            with codecs.open(path, "r", "utf-8") as fileObject:
                for line in fileObject:
                    if u"#" in line:
                        line = line.split(u"#")[0]
                    line = line.strip()
                    if line:
                        yield line


    def passes(self, line):
        args = [
            u"hunspell",
            u"-d",
            self.spellCheckerPath,
            u"-l",
        ]
        hunspell = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        standardOutput, errorOutput = hunspell.communicate(line.encode("utf-8"))
        return not standardOutput.decode("utf-8").strip()


    def analyze(self, line):
        args = [
            u"hunspell",
            u"-d",
            self.spellCheckerPath,
            u"-m",
        ]
        hunspell = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        standardOutput, errorOutput = hunspell.communicate(u"\"{}\"".format(line).encode("utf-8"))
        return standardOutput.decode("utf-8")


    def checkGoodInput(self):
        goodInputFilePath = os.path.join(common.getTestsPath(), u"{}.good".format(self.path))
        for line in self.iterFileLines(goodInputFilePath):
            if not self.passes(line):
                common.error(u"O corrector non aceptou «{}».".format(line))
                details = self.analyze(line)
                common.details(details)
                self.errors += 1


    def checkBadInput(self):
        badInputFilePath = os.path.join(common.getTestsPath(), u"{}.bad".format(self.path))
        for line in self.iterFileLines(badInputFilePath):
            if self.passes(line):
                common.error(u"O corrector aceptou «{}».".format(line))
                common.details(self.analyze(line))
                self.errors += 1


    def run(self, spellCheckerManager):
        self.spellCheckerManager = spellCheckerManager
        self.generateSpellChecker()
        self.checkGoodInput()
        self.checkBadInput()
        self.report()



def findJsonFilePaths(rootPath):
    for parentFolderPath, folderNames, fileNames in os.walk(rootPath):
        for fileName in fileNames:
            if fileName.endswith(".json"):
                yield os.path.join(parentFolderPath, fileName)



def loadTestList():
    tests = []
    testsPath = common.getTestsPath()
    for jsonFilePath in findJsonFilePaths(testsPath):
        testPath = common.getFirstPathRelativeToSecondPathIfWithin(jsonFilePath[:-5], testsPath)
        tests.append(SpellingTest(testPath))
    return tests