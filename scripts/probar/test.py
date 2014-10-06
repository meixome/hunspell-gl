# -*- coding:utf-8 -*-


import common



class Test(object):

    def __init__(self):
        self.errors = 0


    def report(self):
        if self.errors == 0:
            common.output(u"  ✓ Superáronse todas as probas.\n")
        elif self.errors == 1:
            common.output(u"  ✗ Non se pasou unha das probas.\n")
        else:
            common.output(u"  ✗ Non se pasaron {} das probas.\n".format(self.errors))


    def run(self, spellCheckerManager):
        raise Exception("Abstract method")