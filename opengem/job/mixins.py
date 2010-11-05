# from opengem.hazard.job import HazJobMixin
# import opengem.risk.job


class Mixin(object):
    mixins = {}
    def __init__(self, target, mixin):
        print "Constructoring Mixin with target of %s" % target
        self.target = target
        self.mixin = mixin

    def __enter__(self):
        self._load()
        return self

    def __exit__(self, *args):
        self._unload()

    def _load(self):
        print "In _load, self is %s" % self
        if issubclass(self.mixin, type(self)):
            calculation_mode = self.target.params['CALCULATION_MODE']
            self.mixin = self.mixin.mixins[calculation_mode]
        self.target.__class__.__bases__ += (self.mixin,)

        return self.target

    def _unload(self):
        bases = list(self.target.__class__.__bases__)
        bases.remove(self.mixin)
        self.target.__class__.__bases__ = tuple(bases)

    @classmethod
    def register(cls, key, mixin):
        if not key in cls.mixins:
            cls.mixins[key] = mixin

    @classmethod
    def unregister(cls, key):
        del mixins[key]
