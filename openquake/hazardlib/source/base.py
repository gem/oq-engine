# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
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
from dataclasses import dataclass
import numpy
from openquake.baselib import general
from openquake.hazardlib import mfd
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.tom import PoissonTOM
from openquake.hazardlib.calc.filters import magstr, split_source
from openquake.hazardlib.geo import Point
from openquake.hazardlib.geo.surface.planar import build_planar, PlanarSurface
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.source.rupture import (
    ParametricProbabilisticRupture, NonParametricProbabilisticRupture,
    EBRupture)

F64 = numpy.float64

@dataclass
class SourceParam:
    source_id: str
    name: str
    tectonic_region_type: str
    mfd: object
    rupture_mesh_spacing: float
    magnitude_scaling_relationship: object
    rupture_aspect_ratio: float
    temporal_occurrence_model: object


def get_code2cls():
    """
    :returns: a dictionary source code -> source class
    """
    dic = {}
    for cls in general.gen_subclasses(BaseSeismicSource):
        if hasattr(cls, 'code'):
            dic[cls.code] = cls
    return dic


def is_poissonian(src):
    """
    :returns: True if the underlying source is poissonian, false otherwise
    """
    if src.code == b'F':  # multiFault
        return src.infer_occur_rates
    elif src.code == b'N':  # nonParametric
        return False
    return True


def poisson_sample(src, eff_num_ses, seed):
    """
    :param src: a poissonian source
    :param eff_num_ses: number of stochastic event sets * number of samples
    :param seed: stochastic seed
    :yields: triples (rupture, rup_id, num_occurrences)
    """
    rng = numpy.random.default_rng(seed)
    if hasattr(src, 'temporal_occurrence_model'):
        tom = src.temporal_occurrence_model
    else:  # multifault
        tom = PoissonTOM(src.investigation_time)
    rupids = src.offset + numpy.arange(src.num_ruptures)
    if not hasattr(src, 'nodal_plane_distribution'):
        if src.code == b'F':  # multifault
            s = src.get_sections()
            for i, rate in enumerate(src.occur_rates):
                # NB: rng.poisson called inside to save memory
                num_occ = rng.poisson(rate * tom.time_span * eff_num_ses)
                if num_occ == 0:  # skip
                    continue
                idxs = src.rupture_idxs[i]
                if len(idxs) == 1:
                    sfc = s[idxs[0]]
                else:
                    sfc = MultiSurface([s[idx] for idx in idxs])
                hypo = s[idxs[0]].get_middle_point()
                rup = ParametricProbabilisticRupture(
                    src.mags[i], src.rakes[i], src.tectonic_region_type,
                    hypo, sfc, src.occur_rates[i], tom)
                yield rup, rupids[i], num_occ
        else:  # simple or complex fault
            ruptures = list(src.iter_ruptures())
            rates = numpy.array([rup.occurrence_rate for rup in ruptures])
            occurs = rng.poisson(rates * tom.time_span * eff_num_ses)
            for rup, rupid, num_occ in zip(ruptures, rupids, occurs):
                if num_occ:
                    yield rup, rupid, num_occ
        return

    # else (multi)point sources and area sources
    usd = src.upper_seismogenic_depth
    lsd = src.lower_seismogenic_depth
    rar = src.rupture_aspect_ratio
    rup_args = []
    rates = []
    for ps in split_source(src):
        if not hasattr(ps, 'location'):  # unsplit containing a single source
            [ps] = src
        lon, lat = ps.location.x, ps.location.y
        for mag, mag_occ_rate in ps.get_annual_occurrence_rates():
            for np_prob, np in ps.nodal_plane_distribution.data:
                for hc_prob, hc_depth in ps.hypocenter_distribution.data:
                    args = (mag_occ_rate, np_prob, hc_prob,
                            mag, np, lon, lat, hc_depth, ps)
                    rup_args.append(args)
                    rates.append(mag_occ_rate * np_prob * hc_prob)
    eff_rates = numpy.array(rates) * tom.time_span * eff_num_ses
    occurs = rng.poisson(eff_rates)
    for num_occ, args, rupid, rate in zip(occurs, rup_args, rupids, rates):
        if num_occ:
            _, np_prob, hc_prob, mag, np, lon, lat, hc_depth, ps = args
            hc = Point(lon, lat, hc_depth)
            hdd = numpy.array([(1., hc.depth)])
            [[[planar]]] = build_planar(
                ps.get_planin([(1., mag)], [(1., np)]), hdd, lon, lat,
                usd, lsd, rar)
            rup = ParametricProbabilisticRupture(
                mag, np.rake, ps.tectonic_region_type, hc,
                PlanarSurface.from_(planar), rate, tom)
            yield rup, rupid, num_occ


def timedep_sample(src, eff_num_ses, seed):
    """
    :param src: a time-dependent source
    :param eff_num_ses: number of stochastic event sets * number of samples
    :param seed: stochastic seed
    :yields: triples (rupture, rup_id, num_occurrences)
    """
    rng = numpy.random.default_rng(seed)
    rupids = src.offset + numpy.arange(src.num_ruptures)
    if src.code == b'F':  # time-dependent multifault
        s = src.get_sections()
        for i, probs in enumerate(src.probs_occur):
            cdf = numpy.cumsum(probs)
            num_occ = numpy.digitize(rng.random(eff_num_ses), cdf).sum()
            if num_occ == 0:  # ignore non-occurring ruptures
                continue
            idxs = src.rupture_idxs[i]
            if len(idxs) == 1:
                sfc = s[idxs[0]]
            else:
                sfc = MultiSurface([s[idx] for idx in idxs])
            hypo = sfc.get_middle_point()
            pmf = PMF([(p, o) for o, p in enumerate(probs)])
            yield (NonParametricProbabilisticRupture(
                src.mags[i], src.rakes[i], src.tectonic_region_type,
                hypo, sfc, pmf), rupids[i], num_occ)

    else:  # time-dependent nonparametric
        mutex_weight = getattr(src, 'mutex_weight', 1)
        for rup, rupid in zip(src.iter_ruptures(), rupids):
            occurs = rup.sample_number_of_occurrences(eff_num_ses, rng)
            if mutex_weight < 1:
                # consider only the occurrencies below the mutex_weight
                occurs *= (rng.random(eff_num_ses) < mutex_weight)
            num_occ = occurs.sum()
            if num_occ:
                yield rup, rupid, num_occ


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
    id = -1  # to be set
    trt_smr = 0  # set by the engine
    nsites = 1  # set when filtering the source
    splittable = True
    checksum = 0  # set in source_reader
    weight = 0.001  # set in contexts
    esites = 0  # updated in estimate_weight
    offset = 0  # set in fix_src_offset
    trt_smr = -1  # set by the engine
    num_ruptures = 0  # set by the engine
    seed = None  # set by the engine

    @abc.abstractproperty
    def MODIFICATIONS(self):
        pass

    @property
    def trt_smrs(self):
        """
        :returns: a list of integers (usually of 1 element)
        """
        trt_smr = self.trt_smr
        return (trt_smr,) if isinstance(trt_smr, int) else trt_smr

    def serial(self, ses_seed):
        """
        :returns: a random seed derived from source_id and ses_seed
        """
        return zlib.crc32(self.source_id.encode('ascii'), ses_seed)

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

    def iter_meshes(self):
        """
        Yields the meshes underlying the ruptures
        """
        for rup in self.iter_ruptures():
            if isinstance(rup.surface, MultiSurface):
                for surf in rup.surface.surfaces:
                    yield surf.mesh
            else:
                yield rup.surface.mesh

    def sample_ruptures(self, eff_num_ses, ses_seed):
        """
        :param eff_num_ses: number of stochastic event sets * number of samples
        :yields: triples (rupture, trt_smr, num_occurrences)
        """
        seed = self.serial(ses_seed)
        sample = poisson_sample if is_poissonian(self) else timedep_sample
        for rup, rupid, num_occ in sample(self, eff_num_ses, seed):
            if self.smweight < 1 and hasattr(rup, 'occurrence_rate'):
                # defined only for poissonian sources
                # needed to get convergency of the frequency to the rate
                # tested only in oq-risk-tests etna0
                rup.occurrence_rate *= self.smweight
            ebr = EBRupture(rup, self.id, self.trt_smr, num_occ, rupid)
            ebr.seed = ebr.id + ses_seed
            yield ebr

    def get_mags(self):
        """
        :returns: the magnitudes of the ruptures contained in the source
        """
        if hasattr(self, 'get_annual_occurrence_rates'):
            return F64([m for m, r in self.get_annual_occurrence_rates()])
        mags = set()
        if hasattr(self, 'mags'):  # MultiFaultSource
            mags.update(self.mags)
        else:  # nonparametric
            for rup, pmf in self.data:
                mags.add(rup.mag)
        return sorted(mags)

    def get_magstrs(self):
        """
        :returns: the magnitudes of the ruptures contained as strings
        """
        if hasattr(self, 'mags'):  # MultiFaultSource
            mags = {magstr(mag) for mag in self.mags}
        elif hasattr(self, 'data'):  # nonparametric
            mags = {magstr(item[0].mag) for item in self.data}
        else:
            mags = {magstr(item[0]) for item in
                    self.get_annual_occurrence_rates()}
        return sorted(mags)

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

    def __repr__(self):
        """
        String representation of a source, displaying the source class name
        and the source id.
        """
        return '<%s %s, weight=%.2f>' % (
            self.__class__.__name__, self.source_id, self.weight)


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
        self.source_id = source_id
        self.name = name
        self.tectonic_region_type = tectonic_region_type

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

        The list is taken from assigned MFD object (see :meth:
        `openquake.hazardlib.mfd.base.BaseMFD.get_annual_occurrence_rates`)
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
                for mag, occ_rate in self.mfd.get_annual_occurrence_rates()
                if min_rate is None or occ_rate > min_rate]

    def get_min_max_mag(self):
        """
        Get the minimum and maximum magnitudes of the ruptures generated
        by the source from the underlying MFD.
        """
        return self.mfd.get_min_max_mag()

    def modify_set_msr(self, new_msr):
        """
        Updates the MSR originally assigned to the source

        :param new_msr:
            An instance of the :class:`openquake.hazardlib.scalerel.BaseMSR`
        """
        self.magnitude_scaling_relationship = new_msr

    def modify_set_slip_rate(self, slip_rate: float):
        """
        Updates the slip rate assigned to the source

        :param slip_rate:
            The value of slip rate [mm/yr]
        """
        self.slip_rate = slip_rate

    def modify_set_mmax_truncatedGR(self, mmax: float):
        """
        Updates the mmax assigned. This works on for parametric MFDs.s

        :param mmax:
            The value of the new maximum magnitude
        """
        # Check that the current src has a TruncatedGRMFD MFD
        msg = 'This modification works only when the source MFD is a '
        msg += 'TruncatedGRMFD'
        assert self.mfd.__class__.__name__ == 'TruncatedGRMFD', msg
        self.mfd.max_mag

    def modify_recompute_mmax(self, epsilon: float = 0):
        """
        Updates the value of mmax using the msr and the area of the fault

        :param epsilon:
            Number of standard deviations to be added or substracted
        """
        msr = self.magnitude_scaling_relationship
        area = self.get_fault_surface_area()  # area in km^2
        mag = msr.get_median_mag(area=area, rake=self.rake)
        std = msr.get_std_dev_mag(area=area, rake=self.rake)
        self.mfd.max_mag = mag + epsilon * std

    def modify_adjust_mfd_from_slip(self, slip_rate: float, rigidity: float,
                                    constant_term: float = 9.1,
                                    recompute_mmax: float = None):
        """
        :param slip_rate:
            A float defining slip rate [in mm]
        :param rigidity:
            A float defining material rigidity [in GPa]
        :param constant_term:
            Constant term of the equation used to compute log M0 from magnitude
        """
        # Check that the current src has a TruncatedGRMFD MFD
        msg = 'This modification works only when the source MFD is a '
        msg += 'TruncatedGRMFD'
        assert self.mfd.__class__.__name__ == 'TruncatedGRMFD', msg
        # Compute moment
        area = self.get_fault_surface_area() * 1e6  # area in m^2
        rigidity *= 1e9  # rigidity in Pa
        slip_rate *= 1e-3  # slip rate in m
        mo = rigidity * area * slip_rate
        # Update the MFD
        min_mag = self.mfd.min_mag
        max_mag = self.mfd.max_mag
        bin_w = self.mfd.bin_width
        b_val = self.mfd.b_val
        self.mfd = mfd.TruncatedGRMFD.from_moment(min_mag, max_mag, bin_w,
                                                  b_val, mo, constant_term)
