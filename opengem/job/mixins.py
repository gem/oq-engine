class Mixin(object):
    mixins = {}
    def __init__(self, target, mixin, key=""):
        self.key = key.upper() + "_CALCULATION_MODE"
        self.target = target
        self.mixin = mixin

    def __enter__(self):
        return self._load()

    def __exit__(self, *args):
        self._unload()

    def _load(self):
        if issubclass(self.mixin, type(self)):
            calculation_mode = self.target.params[self.key]
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
