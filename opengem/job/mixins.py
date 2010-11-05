class Mixin(object):
    mixins = []
    def __init__(self, target, mixin):
        self.target = target
        self.mixin = mixin

    def __enter__(self):
        self._load()

    def __exit__(self, *args):
        self._unload()

    def _load(self):
        if issubclass(self.mixin, type(self)):
            calculation_mode = self.target.params['calculation_mode']
            mixin_index = self.mixin.mixins.index(calculation_mode)
            self.mixin = self.mixin.mixins[mixin_index]
        self.target.__bases__ += (self.mixin,)

    def _unload(self):
        bases = list(self.target.__bases__)
        bases.remove(self.mixin)
        self.target.__bases__ = tuple(bases)

    @classmethod
    def register(cls, mixin):
        if not mixin in cls.mixins:
            return cls.mixins.append(mixin)

    @classmethod
    def unregister(cls, mixin):
        return mixins.remove(mixin)
