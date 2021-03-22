# The Hazard Library
# Copyright (C) 2012-2021 GEM Foundation
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
import zlib
import numpy
from openquake.hazardlib.geo import Point
from openquake.hazardlib.source.rupture import ParametricProbabilisticRupture

EPS = .01  # used for src.nsites outside the maximum_distance


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
    et_id = 0  # set by the engine
    nsites = 0  # set when filtering the source
    ngsims = 1
    min_mag = 0  # set in get_oqparams and CompositeSourceModel.filter
    splittable = True
    checksum = 0  # set in source_reader

    @abc.abstractproperty
    def MODIFICATIONS(self):
        pass

    @property
    def weight(self):
        """
        Determine the source weight from the number of ruptures
        """
        # NB: for point sources .num_ruptures is preset in preclassical,
        # and it is less than the real number of ruptures if the
        # pointsource_distance is set
        if not self.num_ruptures:
            self.num_ruptures = self.count_ruptures()
        w = self.num_ruptures * self.ngsims * (.1 if self.nsites == EPS else 1)
        if not hasattr(self, 'nodal_plane_distribution'):  # not pointlike
            w *= 10  # increase weight of non point sources
        return w

    @property
    def et_ids(self):
        """
        :returns: a list of source group IDs (usually of 1 element)
        """
        et_id = self.et_id
        return [et_id] if isinstance(et_id, int) else et_id

    def serial(self, ses_seed):
        """
        :returns: a random seed derived from source_id and ses_seed
        """
        return zlib.crc32(self.source_id.encode('ascii'), ses_seed)

    def __init__(self, source_id, name, tectonic_region_type):
        self.source_id = source_id
        self.name = name
        self.tectonic_region_type = tectonic_region_type
        self.et_id = -1  # set by the engine
        self.num_ruptures = 0  # set by the engine
        self.seed = None  # set by the engine
        self.min_mag = 0  # set by the SourceConverter

    def is_gridded(self):
        """
        :returns: True if the source contains only gridded ruptures
        """
        return False

    @abc.abstractmethod
    def iter_ruptures(self, **kwargs):
        """
        Get a generator object that yields probabilistic ruptures the source
        consists of.

        :returns:
            Generator of instances of sublclass of :class:
            `~openquake.hazardlib.source.rupture.BaseProbabilisticRupture`.
        """

    def sample_ruptures(self, eff_num_ses, ses_seed):
        """
        :param eff_num_ses: number of stochastic event sets * number of samples
        :yields: triples (rupture, et_id, num_occurrences)
        """
        seed = self.serial(ses_seed)
        numpy.random.seed(seed)
        for et_id in self.et_ids:
            for rup, num_occ in self._sample_ruptures(eff_num_ses):
                rup.rup_id = seed
                seed += 1
                yield rup, et_id, num_occ

    def _sample_ruptures(self, eff_num_ses):
        tom = getattr(self, 'temporal_occurrence_model', None)
        if tom:  # time-independent source
            yield from self.sample_ruptures_poissonian(eff_num_ses)
        else:  # time-dependent source (nonparametric)
            mutex_weight = getattr(self, 'mutex_weight', 1)
            for rup in self.iter_ruptures():
                occurs = rup.sample_number_of_occurrences(eff_num_ses)
                if mutex_weight < 1:
                    # consider only the occurrencies below the mutex_weight
                    occurs *= (numpy.random.random(eff_num_ses) < mutex_weight)
                num_occ = occurs.sum()
                if num_occ:
                    yield rup, num_occ

    def get_mags(self):
        """
        :returns: the magnitudes of the ruptures contained in the source
        """
        mags = set()
        if hasattr(self, 'get_annual_occurrence_rates'):
            for mag, rate in self.get_annual_occurrence_rates():
                mags.add(mag)
        elif hasattr(self, 'source_file'):
            # unbound UCERFSource
            mags.add(numpy.nan)
        else:  # nonparametric
            for rup, pmf in self.data:
                if rup.mag >= self.min_mag:
                    mags.add(rup.mag)
        return sorted(mags)

    def sample_ruptures_poissonian(self, eff_num_ses):
        """
        :param eff_num_ses: number of stochastic event sets * number of samples
        :yields: pairs (rupture, num_occurrences[num_samples])
        """
        tom = self.temporal_occurrence_model
        if not hasattr(self, 'nodal_plane_distribution'):  # fault
            ruptures = list(self.iter_ruptures())
            rates = numpy.array([rup.occurrence_rate for rup in ruptures])
            occurs = numpy.random.poisson(rates * tom.time_span * eff_num_ses)
            for rup, num_occ in zip(ruptures, occurs):
                if num_occ:
                    yield rup, num_occ
            return
        # else (multi)point sources and area sources
        rup_args = []
        rates = []
        for src in self:
            for mag, mag_occ_rate in src.get_annual_occurrence_rates():
                if mag < self.min_mag:
                    continue
                for np_prob, np in src.nodal_plane_distribution.data:
                    for hc_prob, hc_depth in src.hypocenter_distribution.data:
                        args = (mag_occ_rate, np_prob, hc_prob,
                                mag, np, hc_depth, src)
                        rup_args.append(args)
                        rates.append(mag_occ_rate * np_prob * hc_prob)
        eff_rates = numpy.array(rates) * tom.time_span * eff_num_ses
        occurs = numpy.random.poisson(eff_rates)
        for num_occ, args, rate in zip(occurs, rup_args, rates):
            if num_occ:
                mag_occ_rate, np_prob, hc_prob, mag, np, hc_depth, src = args
                hc = Point(latitude=src.location.latitude,
                           longitude=src.location.longitude,
                           depth=hc_depth)
                surface, _ = src._get_rupture_surface(mag, np, hc)
                rup = ParametricProbabilisticRupture(
                    mag, np.rake, src.tectonic_region_type, hc,
                    surface, rate, tom)
                yield rup, num_occ

    @abc.abstractmethod
    def get_one_rupture(self, ses_seed, rupture_mutex=False):
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

    def to_xml(self):
        """
        Convert the source into an XML string, very useful for debugging
        """
        from openquake.hazardlib import nrml, sourcewriter
        return nrml.to_string(sourcewriter.obj_to_node(self))


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
        scaling_rate = getattr(self, 'scaling_rate', 1)
        return [(mag, occ_rate * scaling_rate)
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

    def get_one_rupture(self, ses_seed, rupture_mutex=False):
        """
        Yields one random rupture from a source
        """
        # The Mutex case is admitted only for non-parametric ruptures
        msg = 'Mutually exclusive ruptures are admitted only in case of'
        msg += ' non-parametric sources'
        assert (not rupture_mutex), msg
        # Set random seed and get the number of ruptures
        num_ruptures = self.count_ruptures()
        seed = self.serial(ses_seed)
        numpy.random.seed(seed)
        idx = numpy.random.choice(num_ruptures)
        # NOTE Would be nice to have a method generating a rupture given two
        # indexes, one for magnitude and one setting the position
        for i, rup in enumerate(self.iter_ruptures()):
            if i == idx:
                if hasattr(self, 'rup_id'):
                    rup.rup_id = self.rup_id
                rup.idx = idx
                return rup
