# -*- coding:utf-8 -*-

import os, sys
import codecs, locale

# See http://stackoverflow.com/a/4546129/939364
sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)



def getModulesSourcePath():
    return os.path.dirname(os.path.realpath(__file__))  + u"/../../src"



# Program starts.

modulesPath = getModulesSourcePath()
fileToClean = sys.argv[1]
inputFiles = sys.argv[2:]

entries = set()
for inputFile in inputFiles:
    with codecs.open(inputFile, "r", "utf-8") as fileObject:
        for line in fileObject.readlines():
            entries.add(line.split(u" ")[0])


newContent = u""
with codecs.open(fileToClean, "r", "utf-8") as fileObject:
    for line in fileObject.readlines():

        strippedLine = line.strip()
        if not strippedLine or strippedLine[0] == u"#":
            newContent += line
            continue

        entry = line.split(u" ")[0].strip()
        if entry not in entries:
            newContent += line
            continue

        print u"Eliminando «{}»…".format(entry)


with codecs.open(fileToClean, "w", "utf-8") as fileObject:
    fileObject.write(newContent)