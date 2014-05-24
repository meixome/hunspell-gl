# -*- coding:utf-8 -*-

import os, shutil, subprocess

import common



class Manager(object):

    def __init__(self):

        self.builtSpellCheckers = {}


    def __enter__(self):
        return self


    def __exit__(self, type, value, traceback):

        for path in self.builtSpellCheckers.iterkeys():
            os.remove(path + u".aff")
            os.remove(path + u".dic")

        try:
            os.rmdir(common.getBuildPath())
        except:
            pass


    def getUnusedCode(self):

        buildPath = common.getBuildPath()

        if not os.path.exists(buildPath):
            return 1

        index = 2
        while os.path.exists(os.path.join(buildPath, u"{}.aff".format(index))):
            index += 1
        return index


    def create(self, config):

        for builtPath, builtConfig in self.builtSpellCheckers.iteritems():
            if config == builtConfig:
                return builtPath

        args = [u"scons",]

        for fileExtension in [u"aff", u"dic", u"rep"]:
            if fileExtension in config:
                args.append(u"{}={}".format(fileExtension, u",".join(config[fileExtension])))

        code = self.getUnusedCode()
        args.append(u"code={}".format(code))

        devNull = open(os.devnull, 'w')
        subprocess.call(args, cwd=common.getRootPath(), stdout=devNull, stderr=subprocess.STDOUT)

        path = os.path.join(common.getBuildPath(), u"{}".format(code))
        self.builtSpellCheckers[path] = config
        return path