# -*- coding:utf-8 -*-

from __future__ import print_function

import os, pickle, time
from xdg.BaseDirectory import save_cache_path


def getModulesSourcePath():
    return os.path.dirname(os.path.realpath(__file__))  + u"/../../src"



class CacheManager(object):

    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CacheManager, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance


    def __init__(self):
        self.cacheFolder = save_cache_path(u"hunspell-gl")
        self.pickleFolder = os.path.join(self.cacheFolder, u"pickle")


    def cachePath(self, resourcePath, objectName):
        return os.path.join(self.pickleFolder, resourcePath, objectName)


    def exists(self, resourcePath, objectName):
        cachePath = self.cachePath(resourcePath, objectName)
        if not os.path.exists(cachePath):
            return False
        fileData = os.stat(cachePath)
        if (time.time() - fileData.st_mtime) > 86400: # Older than 24h.
            return False
        return True


    def load(self, resourcePath, objectName):
        cachePath = self.cachePath(resourcePath, objectName)
        with open(cachePath, "r") as fileObject:
            return pickle.load(fileObject)


    def save(self, resourcePath, objectName, objectData):
        cachePath = self.cachePath(resourcePath, objectName)
        if not os.path.exists(os.path.dirname(cachePath)):
            os.makedirs(os.path.dirname(cachePath))
        with open(cachePath, "w") as fileObject:
            pickle.dump(objectData, fileObject)