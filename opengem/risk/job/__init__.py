""" Mixin proxy for risk jobs """

from opengem.job.mixins import Mixin


#############################
#                           #
# Risk Job Mixin decorators #
#                           #
#############################

def preload(fn):
    """ Preload decorator """
    def preloader(self, *args, **kwargs):
        """A decorator for preload steps that must run on the Jobber"""
        # Do preload stuff

        self.store_region_constraint()
        self.store_sites_and_hazard_curve()
        self.store_exposure_assets()
        self.store_vulnerability_model()

        return fn(self, *args, **kwargs)
    return preloader


def output(fn):
    """ Decorator for output """
    def output_writer(self, *args, **kwargs):
        """ Write the output of a block to memcached. """
        result = fn(self, *args, **kwargs)

        # TODO(chris): Should we use the returned result?
        if result:
            # pylint: disable-msg=W0212
            self._write_output_for_block(self.job_id, self.block_id)
        return result

    return output_writer


class RiskJobMixin(Mixin):
    """ A mixin proxy for Risk jobs """
    mixins = {}

Mixin.register("Risk", RiskJobMixin, order=2)
