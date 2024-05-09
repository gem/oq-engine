# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module :mod:`openquake.hazardlib.gsim.base` defines base classes for
different kinds of :class:`ground shaking intensity models
<GroundShakingIntensityModel>`.
"""
import sys
import abc
import inspect
import warnings
import functools
import toml
import numpy

from openquake.baselib.general import DeprecationWarning
from openquake.baselib.performance import compile
from openquake.hazardlib import const
from openquake.hazardlib.stats import truncnorm_sf
from openquake.hazardlib.gsim.coeffs_table import CoeffsTable
from openquake.hazardlib.contexts import (
    KNOWN_DISTANCES, full_context, ContextMaker)
from openquake.hazardlib.contexts import *  # for backward compatibility


ADMITTED_STR_PARAMETERS = ['DEFINED_FOR_TECTONIC_REGION_TYPE',
                           'DEFINED_FOR_INTENSITY_MEASURE_COMPONENT']
ADMITTED_FLOAT_PARAMETERS = ['DEFINED_FOR_REFERENCE_VELOCITY']
ADMITTED_SET_PARAMETERS = ['DEFINED_FOR_INTENSITY_MEASURE_TYPES',
                           'DEFINED_FOR_STANDARD_DEVIATION_TYPES',
                           'REQUIRES_DISTANCES',
                           'REQUIRES_ATTRIBUTES',
                           'REQUIRES_SITES_PARAMETERS',
                           'REQUIRES_RUPTURE_PARAMETERS']

F64 = numpy.float64
registry = {}  # GSIM name -> GSIM class
gsim_aliases = {}  # GSIM alias -> TOML representation


def add_alias(name, cls, **kw):
    """
    Add a GSIM alias to both gsim_aliases and the registry.
    """
    gsim_aliases[name] = toml.dumps({cls.__name__: kw})
    registry[name] = cls


class NotVerifiedWarning(UserWarning):
    """
    Raised when a non verified GSIM is instantiated
    """


class ExperimentalWarning(UserWarning):
    """
    Raised for GMPEs that are intended for experimental use or maybe subject
    to changes in future version.
    """


class AdaptedWarning(UserWarning):
    """
    Raised for GMPEs that are intended for experimental use or maybe subject
    to changes in future version.
    """


# this is the critical function for the performance of the classical calculator
# the performance is dominated by the CPU cache, i.e. large arrays are slow
# the only way to speedup is to reduce the maximum_distance, then the array
# will become shorter in the N dimension (number of affected sites), or to
# collapse the ruptures, then truncnorm_sf will be called less times
@compile("(float64[:,:,:], float64[:,:], float64, float64[:,:])")
def _set_poes(mean_std, loglevels, phi_b, out):
    L1 = loglevels.size // len(loglevels)
    for m, levels in enumerate(loglevels):
        mL1 = m * L1
        mea, std = mean_std[:, m]  # shape N
        for lvl, iml in enumerate(levels):
            out[mL1 + lvl] = truncnorm_sf(phi_b, (iml - mea) / std)


def _get_poes(mean_std, loglevels, phi_b):
    # returns a matrix of shape (N, L)
    N = mean_std.shape[2]  # shape (2, M, N)
    out = numpy.zeros((loglevels.size, N))  # shape (L, N)
    _set_poes(mean_std, loglevels, phi_b, out)
    return out.T


OK_METHODS = ('compute', 'get_mean_and_stddevs', 'set_poes', 'requires',
              'set_parameters', 'set_tables')


def bad_methods(clsdict):
    """
    :returns: list of not acceptable method names
    """
    bad = []
    for name, value in clsdict.items():
        if name in OK_METHODS or name.startswith('__') and name.endswith('__'):
            pass  # not bad
        elif inspect.isfunction(value) or hasattr(value, '__func__'):
            bad.append(name)
    return bad


class MetaGSIM(abc.ABCMeta):
    """
    A metaclass converting set class attributes into frozensets, to avoid
    mutability bugs without having to change already written GSIMs. Moreover
    it performs some checks against typos.
    """
    def __new__(meta, name, bases, dic):
        if len(bases) > 1:
            raise TypeError('Multiple inheritance is forbidden: %s(%s)' % (
                name, ', '.join(b.__name__ for b in bases)))
        if 'get_mean_and_stddevs' in dic and 'compute' in dic:
            raise TypeError('You cannot define both get_mean_and_stddevs '
                            'and compute in %s' % name)
        bad = bad_methods(dic)
        if bad:
            print('%s cannot contain the methods %s' % (name, bad),
                  file=sys.stderr)
        for k, v in dic.items():
            if (k == 'compute' and v.__annotations__.get("ctx")
                    is not numpy.recarray):
                raise TypeError('%s.compute is not vectorized' % name)
            elif isinstance(v, set):
                dic[k] = frozenset(v)
                if k == 'REQUIRES_DISTANCES':
                    missing = v - KNOWN_DISTANCES
                    if missing:
                        raise ValueError('Unknown distance %s in %s' %
                                         (missing, name))
        cls = super().__new__(meta, name, bases, dic)
        return cls


@functools.total_ordering
class GroundShakingIntensityModel(metaclass=MetaGSIM):
    """
    Base class for all the ground shaking intensity models.

    A Ground Shaking Intensity Model (GSIM) defines a set of equations
    for computing mean and standard deviation of a normal distribution
    representing the variability of an intensity measure (or of its logarithm)
    at a site given an earthquake rupture.

    This class is not intended to be subclassed directly, instead
    the actual GSIMs should subclass :class:`GMPE`.

    Subclasses of both must implement :meth:`get_mean_and_stddevs`
    and all the class attributes with names starting from ``DEFINED_FOR``
    and ``REQUIRES``.
    """
    #: Reference to a
    #: :class:`tectonic region type <openquake.hazardlib.const.TRT>` this GSIM
    #: is defined for. One GSIM can implement only one tectonic region type.
    DEFINED_FOR_TECTONIC_REGION_TYPE = abc.abstractproperty()

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #: this GSIM can
    #: calculate. A set should contain classes from module
    #: :mod:`openquake.hazardlib.imt`.
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = abc.abstractproperty()

    #: Reference to a :class:`intensity measure component type
    #: <openquake.hazardlib.const.IMC>` this GSIM can calculate mean
    #: and standard
    #: deviation for.
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = abc.abstractproperty()

    #: Set of
    #: :class:`standard deviation types <openquake.hazardlib.const.StdDev>`
    #: this GSIM can calculate.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = abc.abstractproperty()

    #: Set of required GSIM attributes
    REQUIRES_ATTRIBUTES = set()

    #: Set of site parameters names this GSIM needs. The set should include
    #: strings that match names of the attributes of a :class:`site
    #: <openquake.hazardlib.site.Site>` object.
    #: Those attributes are then available in the
    #: :class:`SitesContext` object with the same names.
    REQUIRES_SITES_PARAMETERS = abc.abstractproperty()

    #: Set of rupture parameters (excluding distance information) required
    #: by GSIM. Supported parameters are:
    #:
    #: ``mag``
    #:     Magnitude of the rupture.
    #: ``dip``
    #:     Rupture's surface dip angle in decimal degrees.
    #: ``rake``
    #:     Angle describing the slip propagation on the rupture surface,
    #:     in decimal degrees. See :mod:`~openquake.hazardlib.geo.nodalplane`
    #:     for more detailed description of dip and rake.
    #: ``ztor``
    #:     Depth of rupture's top edge in km. See
    #:     :meth:`~openquake.hazardlib.geo.surface.base.BaseSurface.get_top_edge_depth`.
    #:
    #: These parameters are available from the :class:`RuptureContext` object
    #: attributes with same names.
    REQUIRES_RUPTURE_PARAMETERS = abc.abstractproperty()

    #: Set of types of distance measures between rupture and sites. Possible
    #: values are:
    #:
    #: ``rrup``
    #:     Closest distance to rupture surface.  See
    #:     :meth:`~openquake.hazardlib.geo.surface.base.BaseSurface.get_min_distance`.
    #: ``rjb``
    #:     Distance to rupture's surface projection. See
    #:     :meth:`~openquake.hazardlib.geo.surface.base.BaseSurface.get_joyner_boore_distance`.
    #: ``rx``
    #:     Perpendicular distance to rupture top edge projection.
    #:     See :meth:`~openquake.hazardlib.geo.surface.base.BaseSurface.get_rx_distance`.
    #: ``ry0``
    #:     Horizontal distance off the end of the rupture measured parallel to
    #:     strike.
    #:     See :meth:`~openquake.hazardlib.geo.surface.base.BaseSurface.get_ry0_distance`.
    #: ``rcdpp``
    #:     Direct point parameter for directivity effect centered on the site- and earthquake-specific
    #:     average DPP used. See
    #:     :meth:`~openquake.hazardlib.source.rupture.ParametricProbabilisticRupture.get_dppvalue`.
    #: ``rvolc``
    #:     Source to site distance passing through surface projection of volcanic zone.
    #:
    #: All the distances are available from the :class:`DistancesContext`
    #: object attributes with same names. Values are in kilometers.
    REQUIRES_DISTANCES = abc.abstractproperty()

    _toml = ''  # set by valid.gsim
    superseded_by = None
    non_verified = False
    experimental = False
    adapted = False

    @classmethod
    def __init_subclass__(cls):
        stddevtypes = cls.DEFINED_FOR_STANDARD_DEVIATION_TYPES
        if isinstance(stddevtypes, abc.abstractproperty):  # in GMPE
            return
        elif const.StdDev.TOTAL not in stddevtypes:
            raise ValueError(
                '%s.DEFINED_FOR_STANDARD_DEVIATION_TYPES is '
                'not defined for const.StdDev.TOTAL' % cls.__name__)
        for attr, ctable in vars(cls).items():
            if isinstance(ctable, CoeffsTable):
                if not attr.startswith('COEFFS'):
                    raise NameError('%s does not start with COEFFS' % attr)
        registry[cls.__name__] = cls

    def requires(self):
        """
        :returns: ordered tuple with the required parameters except the mag
        """
        tot = set(self.REQUIRES_DISTANCES |
                  self.REQUIRES_RUPTURE_PARAMETERS |
                  self.REQUIRES_SITES_PARAMETERS)
        return tuple(sorted(tot))

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        cls = self.__class__
        if cls.superseded_by:
            msg = '%s is deprecated - use %s instead' % (
                cls.__name__, cls.superseded_by.__name__)
            warnings.warn(msg, DeprecationWarning)
        if cls.non_verified:
            msg = ('%s is not independently verified - the user is liable '
                   'for their application') % cls.__name__
            warnings.warn(msg, NotVerifiedWarning)
        if cls.experimental:
            msg = ('%s is experimental and may change in future versions - '
                   'the user is liable for their application') % cls.__name__
            warnings.warn(msg, ExperimentalWarning)
        if cls.adapted:
            msg = ('%s is not intended for general use and the behaviour '
                   'may not be as expected - '
                   'the user is liable for their application') % cls.__name__
            warnings.warn(msg, AdaptedWarning)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Calculate and return mean value of intensity distribution and it's
        standard deviation.

        Method must be implemented by subclasses.

        :param sites:
            Instance of :class:`openquake.hazardlib.site.SiteCollection`
            with parameters of sites
            collection assigned to respective values as numpy arrays.
            Only those attributes that are listed in class'
            :attr:`REQUIRES_SITES_PARAMETERS` set are available.
        :param rup:
            Instance of :class:`openquake.hazardlib.source.rupture.BaseRupture`
            with parameters of a rupture
            assigned to respective values. Only those attributes that are
            listed in class' :attr:`REQUIRES_RUPTURE_PARAMETERS` set are
            available.
        :param dists:
            Instance of :class:`DistancesContext` with values of distance
            measures between the rupture and each site of the collection
            assigned to respective values as numpy arrays. Only those
            attributes that are listed in class' :attr:`REQUIRES_DISTANCES`
            set are available.
        :param imt:
            An instance (not a class) of intensity measure type.
            See :mod:`openquake.hazardlib.imt`.
        :param stddev_types:
            List of standard deviation types, constants from
            :class:`openquake.hazardlib.const.StdDev`.
            Method result value should include
            standard deviation values for each of types in this list.

        :returns:
            Method should return a tuple of two items. First item should be
            a numpy array of floats -- mean values of respective component
            of a chosen intensity measure type, and the second should be
            a list of numpy arrays of standard deviation values for the same
            single component of the same single intensity measure type, one
            array for each type in ``stddev_types`` parameter, preserving
            the order.

        Combining interface to mean and standard deviation values in a single
        method allows to avoid redoing the same intermediate calculations
        if there are some shared between stddev and mean formulae without
        resorting to keeping any sort of internal state (and effectively
        making GSIM not reenterable).

        However it is advised to split calculation of mean and stddev values
        and make ``get_mean_and_stddevs()`` just combine both (and possibly
        compute interim steps).
        """
        # mean and stddevs by calling the underlying .compute method
        N = len(sites)
        mean = numpy.zeros((1, N))
        sig = numpy.zeros((1, N))
        tau = numpy.zeros((1, N))
        phi = numpy.zeros((1, N))
        if sites is not rup or dists is not rup:
            # convert three old-style contexts to a single new-style context
            ctx = full_context(sites, rup, dists)
        else:
            ctx = rup  # rup is already a good object
        if self.compute.__annotations__.get("ctx") is numpy.recarray:
            cmaker = ContextMaker('*', [self], {'imtls': {imt.string: [0]}})
            if not isinstance(ctx, numpy.ndarray):
                ctx = cmaker.recarray([ctx])
        self.compute(ctx, [imt], mean, sig, tau, phi)
        stddevs = []
        for stddev_type in stddev_types:
            if stddev_type == const.StdDev.TOTAL:
                stddevs.append(sig[0])
            elif stddev_type == const.StdDev.INTER_EVENT:
                stddevs.append(tau[0])
            elif stddev_type == const.StdDev.INTRA_EVENT:
                stddevs.append(phi[0])
        return mean[0], stddevs

    def __lt__(self, other):
        """
        The GSIMs are ordered according to string representation
        """
        return str(self) < str(other)

    def __eq__(self, other):
        """
        The GSIMs are equal if their string representations are equal
        """
        return str(self) == str(other)

    def __hash__(self):
        """
        We use the __str__ representation as hash: it means that we can
        use equivalently GSIM instances or strings as dictionary keys.
        """
        return hash(str(self))

    def __repr__(self):
        """
        String representation for GSIM instances in TOML format.
        """
        if self._toml:
            return self._toml
        return '[%s]' % self.__class__.__name__


def to_distribution_values(vals, imt):
    """
    :returns: the logarithm of the values unless the IMT is MMI
    """
    if str(imt) == 'MMI':
        return vals
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return numpy.log(vals)


class GMPE(GroundShakingIntensityModel):
    """
    Ground-Motion Prediction Equation is a subclass of generic
    :class:`GroundShakingIntensityModel` with a distinct feature
    that the intensity values are log-normally distributed.

    Method :meth:`~GroundShakingIntensityModel.get_mean_and_stddevs`
    of actual GMPE implementations is supposed to return the mean
    value as a natural logarithm of intensity.
    """
    def set_parameters(self):
        """
        Combines the parameters of the GMPE provided at the construction level
        with the ones originally assigned to the backbone modified GMPE.
        """
        for key in (ADMITTED_STR_PARAMETERS + ADMITTED_FLOAT_PARAMETERS +
                    ADMITTED_SET_PARAMETERS):
            try:
                val = getattr(self.gmpe, key)
            except AttributeError:
                pass
            else:
                setattr(self, key, val)

    def compute(self, ctx: numpy.recarray, imts, mean, sig, tau, phi):
        """
        :param ctx: a RuptureContext object or a numpy recarray of size N
        :param imts: a list of M Intensity Measure Types
        :param mean: an array of shape (M, N) for the means
        :param sig: an array of shape (M, N) for the TOTAL stddevs
        :param tau: an array of shape (M, N) for the INTER_EVENT stddevs
        :param phi: an array of shape (M, N) for the INTRA_EVENT stddevs

        To be overridden in subclasses with a procedure filling the
        arrays and returning None.
        """
        raise NotImplementedError

    def set_poes(self, mean_std, cmaker, ctx, out):
        """
        Calculate and return probabilities of exceedance (PoEs) of one or more
        intensity measure levels (IMLs) of one intensity measure type (IMT)
        for one or more pairs "site -- rupture".

        :param mean_std:
            An array of shape (2, M, N) with mean and standard deviations
            for the sites and intensity measure types
        :param cmaker:
            A ContextMaker instance, used only in nhsm_2014
        :param ctx:
            A recarray used only in  avg_poe_gmpe
        :param out:
            An array of PoEs of shape (N, L) to be filled
        :raises ValueError:
            If truncation level is not ``None`` and neither non-negative
            float number, and if ``imts`` dictionary contain wrong or
            unsupported IMTs (see :attr:`DEFINED_FOR_INTENSITY_MEASURE_TYPES`).
        """
        loglevels = cmaker.loglevels.array
        phi_b = cmaker.phi_b
        M, L1 = loglevels.shape
        if hasattr(self, 'weights_signs'):  # for nshmp_2014, case_72
            adj = cmaker.adj[self][cmaker.slc]
            outs = []
            weights, signs = zip(*self.weights_signs)
            for s in signs:
                ms = numpy.array(mean_std)  # make a copy
                for m in range(len(loglevels)):
                    ms[0, m] += s * adj
                outs.append(_get_poes(ms, loglevels, phi_b))
            out[:] = numpy.average(outs, weights=weights, axis=0)
        elif hasattr(self, "mixture_model"):
            for f, w in zip(self.mixture_model["factors"],
                            self.mixture_model["weights"]):
                mean_stdi = numpy.array(mean_std)  # a copy
                mean_stdi[1] *= f  # multiply stddev by factor
                out[:] += w * _get_poes(mean_stdi, loglevels, phi_b)
        else:  # regular case
            _set_poes(mean_std, loglevels, phi_b, out.T)
        imtweight = getattr(self, 'weight', None)  # ImtWeight or None
        for m, imt in enumerate(cmaker.imtls):
            mL1 = m * L1
            if imtweight and imtweight.dic.get(imt) == 0:
                # set by the engine when parsing the gsim logictree
                # when 0 ignore the contribution: see _build_branches
                out[:, mL1:mL1 + L1] = 0
