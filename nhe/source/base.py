"""
Module :mod:`nhe.source.base` defines a base class for seismic sources.
"""
import abc

from nhe import const


class SourceError(Exception):
    """

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
    :param trt:
        Source's tectonic regime. See :class:`const.TRT`.
    :param mfd:
        Magnitude-Frequency distribution for the source. See :mod:`nhe.mfd`.
    :raises SourceError:
        If ``tectonic_region_type`` is wrong/unknown.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, source_id, name, trt, mfd):
        if not const.TRT.is_valid(trt):
            raise SourceError('unknown tectonic region type %s' % trt)
        self.source_id = source_id
        self.name = name
        self.tectonic_region_type = trt
        self.mfd = mfd

    @abc.abstractmethod
    def iter_ruptures(self, temporal_occurrence_model):
        """
        Get a generator object that yields ruptures the source consists of.

        :param temporal_occurrence_model:
            An instance of :class:`nhe.common.tom.PoissonTOM`.
        :returns:
            Generator of instances of :class:`nhe.source.rupture.Rupture`.
        """


class Rupture(object):
    """
    Probabilistic rupture object represents a single earthquake rupture
    associated to a probability of occurrence value.

    :param source:
        Seismic source the rupture belongs to. An instance of one of subclasses
        of :class:`nhe.source.base.SeismicSource`.
    :param mag:
        Magnitude of the rupture.
    :param rake:
        Rupture propagation direction in degrees.
    :param hypocenter:
        A :class:`~nhe.common.geo.Point`, rupture's hypocenter.
    :param probability:
        A probability of the rupture to occur within some time span. The value
        should take into account the probabilities of these exact nodal plane,
        magnitude and hypocenter, as well as a probability of occurrence within
        a given time span (obtained from :mod:`temporal occurrence model
        <nhe.common.tom>`).
    """
    def __init__(self, source, mag, rake, hypocenter, probability, surface):
        assert mag > 0
        assert hypocenter.depth > 0
        assert 0 < probability <= 1
        self.source = source
        self.mag = mag
        self.rake = rake
        self.hypocenter = hypocenter
        self.probability = probability
        self.surface = surface
