"""
Module :mod:`nhe.source.base` defines a base class for seismic sources.
"""
import abc

from nhe import const


class SourceError(Exception):
    """
    An error happened during creation of seismic source or earthquake rupture
    object.
    """

class SeismicSource(object):
    """
    Seismic Source is an object representing geometry and activity rate
    of a structure generating seismicity.

    :param source_id:
        Some (numeric or literal) source identifier. Supposed to be unique
        within the source model.
    :param name:
        String, a human-readable name of the source.
    :param tectonic_region_type:
        Source's tectonic regime. See :class:`const.TRT`.
    :param mfd:
        Magnitude-Frequency distribution for the source. See :mod:`nhe.mfd`.
    :raises SourceError:
        If ``tectonic_region_type`` is wrong/unknown.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, source_id, name, tectonic_region_type, mfd):
        if not const.TRT.is_valid(tectonic_region_type):
            raise SourceError('unknown tectonic region type %r' %
                              tectonic_region_type)
        self.source_id = source_id
        self.name = name
        self.tectonic_region_type = tectonic_region_type
        self.mfd = mfd

    @abc.abstractmethod
    def iter_ruptures(self, temporal_occurrence_model):
        """
        Get a generator object that yields probabilistic ruptures the source
        consists of.

        :param temporal_occurrence_model:
            Temporal occurrence model (supposedly
            :class:`nhe.tom.PoissonTOM`). It is passed intact
            to the probabilistic rupture constructor.
        :returns:
            Generator of instances
            of :class:`~nhe.source.rupture.ProbabilisticRupture`.
        """
