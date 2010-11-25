from openquake.job.mixins import Mixin


class HazJobMixin(Mixin):
    mixins = {}


Mixin.register("Hazard", HazJobMixin, order=1)

