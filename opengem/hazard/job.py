from opengem.job.mixins import Mixin
from opengem.hazard import opensha

Mixin.register(HazJobMixin)
HazJobMixin.register(opensha.MonteCarloMixin)


class HazJobMixin(Mixin):
    mixins = []
