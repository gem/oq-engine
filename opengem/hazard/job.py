from opengem.job.mixins import Mixin

Mixin.register(HazJobMixin)
HazJobMixin.register(MonteCarloMixin)


class HazJobMixin(Mixin):
    mixins = []


class MonteCarloMixin:
    def preload(self, fn):
        def preloader(self, *args, *kwargs):
            return fn(*args, **kwargs)

        return preloader

    @preload
    def execute():
        pass
