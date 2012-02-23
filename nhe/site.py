import const

# TODO: document module and Site class


class Site(object):
    __slots__ = 'vs30 vs30type z1pt0 z2pt5'.split()

    def __init__(self, vs30, vs30type, z1pt0, z2pt5):
        # TODO: add validity checks
        self.vs30 = vs30
        self.vs30type = vs30type
        self.z1pt0 = z1pt0
        self.z2pt5 = z2pt5
