""" The hazard job mixin proxy. """

from openquake.job.mixins import Mixin


class HazJobMixin(Mixin):
    """ Proxy mixin for mixing in hazard job behaviour """
    mixins = {}


Mixin.register("Hazard", HazJobMixin, order=1)
