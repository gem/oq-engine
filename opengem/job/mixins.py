class Mixin(object):
    __mixins = []

    def __init__(self, target, mixin)
        self.target = target
        self.mixin = mixin

    def __enter__(self):
        self._load()

    def __exit__(self):
        self._unload()

    def _load():
        self.target.__bases__ += (self.mixin,)

    def _unload():
        bases = list(self.target.__bases__)
        bases.remove(self.mixin)
        self.target.__bases__ = tuple(bases)


    @classmethod
    def register(cls, mixin):
        if not cls.__mixins.get(mixin, None):
            cls.__mixins.append(mixin)
        return cls.__mixins[mixin]

    @classmethod
    def unregister(cls, mixin):
        return __mixins.remove(mixin)

    @classmethod
    def mixins(cls)
        return cls.__mixins
