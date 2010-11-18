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
            self._proxied_mixin()

        self.target.__class__.__bases__ += (self.mixin,)
        return self.target

    def _unload(self):
        bases = list(self.target.__class__.__bases__)
        bases.remove(self.mixin)
        self.target.__class__.__bases__ = tuple(bases)

    def _proxied_mixin(self):
        calculation_mode = self.target.params[self.key]
        self.mixin = self.mixin.mixins[calculation_mode]['mixin']

    @classmethod
    def ordered_mixins(cls):
        return [(k, v['mixin'])
                 for (k, v)
                 in sorted(cls.mixins.items(), key=lambda x: x[1]['order'])]

    @classmethod
    def register(cls, key, mixin, order=0):
        if not key in cls.mixins:
            cls.mixins[key] = {'mixin': mixin, 'order': order }

    @classmethod
    def unregister(cls, key):
        del mixins[key]
