# -*- coding:utf-8 -*-

import os, sys
import codecs, locale
import common, spellchecker, spelling, syntax

# See http://stackoverflow.com/a/4546129/939364
sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)


def loadBuiltInTestList():
    builtInTests = []
    builtInTests.extend(spelling.loadTestList())
    builtInTests.extend(syntax.loadTestList())
    return builtInTests


# Program starts.

testsPath = common.getTestsPath()
builtInTests = loadBuiltInTestList()

with spellchecker.Manager() as spellCheckerManager:
    for parameter in [parameter.decode('UTF-8') for parameter in sys.argv[1:]]:
        testPath = common.getFirstPathRelativeToSecondPathIfWithin(parameter, testsPath)
        executedTests = 0
        for test in builtInTests:
            if test.path.startswith(testPath):
                print u":: Executando «{path}»…".format(path=test.path)
                test.run(spellCheckerManager)
                executedTests += 1
        if executedTests == 0:
            print u":: Non existe ningunha proba para «{path}».".format(path=testPath)