# The Hazard Library
# Copyright (C) 2012-2019 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.source.base` defines a base class for
seismic sources.
"""
import abc
import math
import numpy
from openquake.baselib.slots import with_slots


@with_slots
class BaseSeismicSource(metaclass=abc.ABCMeta):
    """
    Base class representing a seismic source, that is a structure generating
    earthquake ruptures.

    :param source_id:
        Some (numeric or literal) source identifier. Supposed to be unique
        within the source model.
    :param name:
        String, a human-readable name of the source.
    :param tectonic_region_type:
        Source's tectonic regime. See :class:`openquake.hazardlib.const.TRT`.
    """
    _slots_ = ['source_id', 'name', 'tectonic_region_type',
               'src_group_id', 'num_ruptures', 'id', 'min_mag']
    RUPTURE_WEIGHT = 1.  # overridden in (Multi)PointSource, AreaSource
    ngsims = 1
    min_mag = 0  # set in get_oqparams and CompositeSourceModel.filter
    splittable = True

    @abc.abstractproperty
    def MODIFICATIONS(self):
        pass

    @property
    def weight(self):
        """
        Determine the source weight from the number of ruptures, by
        multiplying with the scale factor RUPTURE_WEIGHT
        """
        if not self.num_ruptures:
            self.num_ruptures = self.count_ruptures()
        # (MS) the weight is proportional to the number of ruptures and GSIMs
        # the relation to the number of sites is unclear, but for sure less
        # than linear and I am using a sqrt here (totally made up but good)
        return (self.num_ruptures * self.RUPTURE_WEIGHT *
                math.sqrt(self.nsites) * self.ngsims)

    @property
    def nsites(self):
        """
        :returns: the number of sites affected by this source
        """
        try:
            # the engine sets self.indices when filtering the sources
            return len(self.indices)
        except AttributeError:
            # this happens in several hazardlib tests, therefore we return
            # a fake number of affected sites to avoid changing all tests
            return 1

    @property
    def src_group_ids(self):
        """
        :returns: a list of source group IDs (usually of 1 element)
        """
        grp_id = getattr(self, 'src_group_id', [0])
        return [grp_id] if isinstance(grp_id, int) else grp_id

    def __init__(self, source_id, name, tectonic_region_type):
        self.source_id = source_id
        self.name = name
        self.tectonic_region_type = tectonic_region_type
        self.src_group_id = 0  # set by the engine
        self.num_ruptures = 0  # set by the engine
        self.seed = None  # set by the engine
        self.id = None  # set by the engine

    @abc.abstractmethod
    def iter_ruptures(self):
        """
        Get a generator object that yields probabilistic ruptures the source
        consists of.

        :returns:
            Generator of instances of sublclass of :class:
            `~openquake.hazardlib.source.rupture.BaseProbabilisticRupture`.
        """

    def sample_ruptures(self, eff_num_ses, ir_monitor):
        """
        :param eff_num_ses: number of stochastic event sets * number of samples
        :param ir_monitor: a monitor object for .iter_ruptures()
        :yields: pairs (rupture, num_occurrences[num_samples])
        """
        mutex_weight = getattr(self, 'mutex_weight', 1)
        with ir_monitor:
            ruptures = list(self.iter_ruptures())
        tom = getattr(self, 'temporal_occurrence_model', None)
        serials = numpy.arange(self.serial, self.serial + self.num_ruptures)

        if tom:  # time-independent source
            rates = numpy.array([rup.occurrence_rate for rup in ruptures])
            numpy.random.seed(self.serial)
            occurs = numpy.random.poisson(rates * tom.time_span * eff_num_ses)
            for rup, serial, num_occ in zip(ruptures, serials, occurs):
                if num_occ:
                    rup.serial = serial  # used as seed
                    yield rup, num_occ
        else:  # time-dependent source
            for rup, serial in zip(ruptures, serials):
                numpy.random.seed(serial)
                occurs = rup.sample_number_of_occurrences(eff_num_ses)
                if mutex_weight < 1:
                    # consider only the occurrencies below the mutex_weight
                    occurs *= (numpy.random.random(eff_num_ses) < mutex_weight)
                num_occ = occurs.sum()
                if num_occ:
                    rup.serial = serial  # used as seed
                    yield rup, num_occ

    @abc.abstractmethod
    def get_one_rupture(self, rupture_mutex=False):
        """
        Yields one random rupture from a source
        """

    def __iter__(self):
        """
        Override to implement source splitting
        """
        yield self

    @abc.abstractmethod
    def count_ruptures(self):
        """
        Return the number of ruptures that will be generated by the source.
        """

    @abc.abstractmethod
    def get_min_max_mag(self):
        """
        Return minimum and maximum magnitudes of the ruptures generated
        by the source.
        """

    def modify(self, modification, parameters):
        """
        Apply a single modificaton to the source parameters
        Reflects the modification method and calls it passing ``parameters``
        as keyword arguments.

        Modifications can be applied one on top of another. The logic
        of stacking modifications is up to a specific source implementation.

        :param modification:
            String name representing the type of modification.
        :param parameters:
            Dictionary of parameters needed for modification.
        :raises ValueError:
            If ``modification`` is missing from the attribute `MODIFICATIONS`.
        """
        if modification not in self.MODIFICATIONS:
            raise ValueError('Modification %s is not supported by %s' %
                             (modification, type(self).__name__))
        meth = getattr(self, 'modify_%s' % modification)
        meth(**parameters)


@with_slots
class ParametricSeismicSource(BaseSeismicSource, metaclass=abc.ABCMeta):
    """
    Parametric Seismic Source generates earthquake ruptures from source
    parameters, and associated probabilities of occurrence are defined through
    a magnitude frequency distribution and a temporal occurrence model.

    :param mfd:
        Magnitude-Frequency distribution for the source.
        See :mod:`openquake.hazardlib.mfd`.
    :param rupture_mesh_spacing:
        The desired distance between two adjacent points in source's
        ruptures' mesh, in km. Mainly this parameter allows to balance
        the trade-off between time needed to compute the :meth:`distance
        <openquake.hazardlib.geo.surface.base.BaseSurface.get_min_distance>`
        between the rupture surface and a site and the precision of that
        computation.
    :param magnitude_scaling_relationship:
        Instance of subclass of
        :class:`openquake.hazardlib.scalerel.base.BaseMSR` to
        describe how does the area of the rupture depend on magnitude and rake.
    :param rupture_aspect_ratio:
        Float number representing how much source's ruptures are more wide
        than tall. Aspect ratio of 1 means ruptures have square shape,
        value below 1 means ruptures stretch vertically more than horizontally
        and vice versa.
    :param temporal_occurrence_model:
        Instance of
        :class:`openquake.hazardlib.tom.PoissonTOM` defining temporal
        occurrence model for calculating rupture occurrence probabilities

    :raises ValueError:
        If either rupture aspect ratio or rupture mesh spacing is not positive
        (if not None).
    """

    _slots_ = BaseSeismicSource._slots_ + '''mfd rupture_mesh_spacing
    magnitude_scaling_relationship rupture_aspect_ratio
    temporal_occurrence_model'''.split()

    def __init__(self, source_id, name, tectonic_region_type, mfd,
                 rupture_mesh_spacing, magnitude_scaling_relationship,
                 rupture_aspect_ratio, temporal_occurrence_model):
        super().__init__(source_id, name, tectonic_region_type)

        if rupture_mesh_spacing is not None and not rupture_mesh_spacing > 0:
            raise ValueError('rupture mesh spacing must be positive')

        if rupture_aspect_ratio is not None and not rupture_aspect_ratio > 0:
            raise ValueError('rupture aspect ratio must be positive')

        self.mfd = mfd
        self.rupture_mesh_spacing = rupture_mesh_spacing
        self.magnitude_scaling_relationship = magnitude_scaling_relationship
        self.rupture_aspect_ratio = rupture_aspect_ratio
        self.temporal_occurrence_model = temporal_occurrence_model

    def get_annual_occurrence_rates(self, min_rate=0):
        """
        Get a list of pairs "magnitude -- annual occurrence rate".

        The list is taken from assigned MFD object
        (see :meth:`openquake.hazardlib.mfd.base.BaseMFD.get_annual_occurrence_rates`)
        with simple filtering by rate applied.

        :param min_rate:
            A non-negative value to filter magnitudes by minimum annual
            occurrence rate. Only magnitudes with rates greater than that
            are included in the result list.
        :returns:
            A list of two-item tuples -- magnitudes and occurrence rates.
        """
        return [(mag, occ_rate)
                for (mag, occ_rate) in self.mfd.get_annual_occurrence_rates()
                if (min_rate is None or occ_rate > min_rate) and
                mag >= self.min_mag]

    def get_min_max_mag(self):
        """
        Get the minimum and maximum magnitudes of the ruptures generated
        by the source from the underlying MFD.
        """
        min_mag, max_mag = self.mfd.get_min_max_mag()
        return max(self.min_mag, min_mag), max_mag

    def __repr__(self):
        """
        String representation of a source, displaying the source class name
        and the source id.
        """
        return '<%s %s>' % (self.__class__.__name__, self.source_id)

    def get_one_rupture(self, rupture_mutex=False):
        """
        Yields one random rupture from a source
        """
        # The Mutex case is admitted only for non-parametric ruptures
        msg = 'Mutually exclusive ruptures are admitted only in case of'
        msg += ' non-parametric sources'
        assert (not rupture_mutex), msg
        # Set random seed and get the number of ruptures
        num_ruptures = self.count_ruptures()
        numpy.random.seed(self.seed)
        idx = numpy.random.choice(num_ruptures)
        # NOTE Would be nice to have a method generating a rupture given two
        # indexes, one for magnitude and one setting the position
        for i, rup in enumerate(self.iter_ruptures()):
            if i == idx:
                if hasattr(self, 'serial'):
                    rup.serial = self.serial
                rup.idx = idx
                return rup
