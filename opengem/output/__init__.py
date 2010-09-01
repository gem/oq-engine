

class SimpleOutput(object):
    def serialize(self, someiterable):
        for somekey, somevalue in someiterable.items():
            print "%s : %s" % (somekey, somevalue)