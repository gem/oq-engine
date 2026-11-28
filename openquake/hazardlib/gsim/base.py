# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2026 GEM Foundation
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
import os
import sys
import abc
import ast
import inspect
import warnings
import functools
import toml
import numpy

from openquake.baselib.general import DeprecationWarning
from openquake.hazardlib import const
from openquake.hazardlib.const import KNOWN_DISTANCES
from openquake.hazardlib.gsim.coeffs_table import CoeffsTable
from openquake.hazardlib.gsim.backbone import (
    adjustment_options, fix_toml, generate_compute, get_central_key,
    _normalize_option)


ADMITTED_STR_PARAMETERS = ['DEFINED_FOR_TECTONIC_REGION_TYPE',
                           'DEFINED_FOR_INTENSITY_MEASURE_COMPONENT']
ADMITTED_FLOAT_PARAMETERS = ['DEFINED_FOR_REFERENCE_VELOCITY']
ADMITTED_SET_PARAMETERS = ['DEFINED_FOR_INTENSITY_MEASURE_TYPES',
                           'DEFINED_FOR_STANDARD_DEVIATION_TYPES',
                           'REQUIRES_DISTANCES',
                           'REQUIRES_ATTRIBUTES',
                           'REQUIRES_SITES_PARAMETERS',
                           'REQUIRES_RUPTURE_PARAMETERS']

F32 = numpy.float32
F64 = numpy.float64
registry = {}  # GSIM name -> GSIM class
gsim_aliases = {}  # GSIM alias -> TOML representation


def add_alias(name, cls, **kw):
    """
    Add a GSIM alias to both gsim_aliases and the registry.
    """
    gsim_aliases[name] = toml.dumps({cls.__name__: kw})
    registry[name] = lambda: cls(**kw)


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

# cache warnings, so that they are displayed only once

@functools.lru_cache()
def warn_superseded_by(cls):
    if cls.superseded_by:
        msg = '%s is deprecated - use %s instead' % (
            cls.__name__, cls.superseded_by.__name__)
        warnings.warn(msg, DeprecationWarning)


@functools.lru_cache()
def warn_non_verified(cls):
    if cls.non_verified:
        msg = ('%s is not independently verified - the user is liable '
               'for their application') % cls.__name__
        warnings.warn(msg, NotVerifiedWarning)


@functools.lru_cache()
def warn_experimental(cls):
    if cls.experimental:
        msg = ('%s is experimental and may change in future versions - '
               'the user is liable for their application') % cls.__name__
        warnings.warn(msg, ExperimentalWarning)


@functools.lru_cache()
def warn_adapted(cls):
    if cls.adapted:
        msg = ('%s is not intended for general use and the behaviour '
               'may not be as expected - '
               'the user is liable for their application') % cls.__name__
        warnings.warn(msg, AdaptedWarning)


OK_METHODS = ('compute', 'compute_adj', 'update_adj', 'set_poes', 'requires',
              'set_parameters')


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
    mutability bugs without having to change already written GSIMs. It also
    generates the compute method of the classes declaring ``compute_adj``
    and ``update_adj`` and performs some checks against typos.
    """
    def __new__(meta, name, bases, dic):
        if len(bases) > 1:
            raise TypeError('Multiple inheritance is forbidden: %s(%s)' % (
                name, ', '.join(b.__name__ for b in bases)))
        bad = bad_methods(dic)
        if bad:
            sys.exit('%s cannot contain the methods %s' % (name, bad))
        if '__init__' in dic:
            params = inspect.signature(dic['__init__']).parameters
            for param in params.values():
                if param.default is None:
                    raise TypeError(
                        f"{name}.{param.name} must default to '' "
                        "instead of None for TOML serialization")
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
        if 'compute' in dic:
            if 'compute_adj' in dic or 'update_adj' in dic:
                raise TypeError(f'{name} cannot define both compute and '
                                'compute_adj or update_adj')
            # A plain compute method opts out of sharing the computation.
            # update_adj is kept, since the inherited compute of a parent
            # still needs the options of its adjustment in kwargs.
            dic['compute_adj'] = None
        elif bases and ('compute_adj' in dic or 'update_adj' in dic):
            # Generate compute from the methods, inheriting the missing one
            base = bases[0]
            compute_adj = dic.get('compute_adj',
                                  getattr(base, 'compute_adj', None))
            update_adj = dic.get('update_adj',
                                 getattr(base, 'update_adj', None))
            if compute_adj is None or update_adj is None:
                raise TypeError(f'{name} must define both compute_adj and '
                                'update_adj to share its computation')
            dic['compute_adj'] = compute_adj
            dic['update_adj'] = update_adj
            dic['compute'] = generate_compute(compute_adj, update_adj)
        cls = super().__new__(meta, name, bases, dic)
        return cls

    def __call__(cls, *, basedir='', **kwargs):
        mixture_model = kwargs.pop('mixture_model', None)
        for name, value in kwargs.items():
            kwargs[name] = value = _normalize_option(value)
            if value is None:
                raise TypeError(
                    f"{cls.__name__}.{name} must use '' instead of None "
                    "for TOML serialization")
            try:
                if ast.literal_eval(repr(value)) == value:
                    continue
            except (ValueError, SyntaxError, RecursionError):
                pass
            raise ValueError(f'{cls.__name__}.{name} must be a Python literal')
        if 'weight' in kwargs:  # AvgPoeGMPE
            w = kwargs.pop('weight')
            self = type.__call__(cls, **kwargs)
            kwargs['weight'] = w
        else:
            self = type.__call__(cls, **kwargs)
        self.kwargs = kwargs
        self._toml = toml.dumps(
            {cls.__name__: fix_toml(kwargs, basedir)}).strip()
        if hasattr(self, 'gmpe_table'):
            # used in NGAEast to set the full pathname
            table = self.gmpe_table
            self.kwargs['gmpe_table'] = (
                os.fspath(table) if table is not None else None)
        if cls.update_adj is not None:
            # Store the constructor defaults of the adjustment options,
            # which kwargs lacks when the caller omits them. Options that
            # the constructor does not name (ModifiableGMPE) get None.
            params = inspect.signature(cls.__init__).parameters
            for name in adjustment_options(cls.update_adj):
                default = params[name].default if name in params else None
                kwargs.setdefault(name, default)
            # Snapshot constructor options before callers can reuse them.
            # NB: the key is computed once, at construction time, so a
            # GSIM must not be modified after it is built, otherwise
            # branches with different predictions could share the same
            # computation in ContextMaker.get_mean_stds.
            self.central_key = get_central_key(self)
        if mixture_model is not None:
            self.mixture_model = mixture_model

        warn_superseded_by(cls)
        warn_non_verified(cls)
        warn_experimental(cls)
        warn_adapted(cls)

        return self


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

    Subclasses of both must implement :meth:`compute`
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
    REQUIRES_DISTANCES = abc.abstractproperty()

    _toml = ''  # set by valid.gsim
    superseded_by = None
    non_verified = False
    experimental = False
    adapted = False
    conditional = False  # must be instantiated from ModifiableGMPE
    from_mgmpe = False  # instantiated using ModifiableGMPE
    # Set by the classes sharing their computation across branches
    compute_adj = None
    update_adj = None

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

    def __lt__(self, other):
        """
        The GSIMs are ordered according to string representation
        """
        return str(self) < str(other)

    def __eq__(self, other):
        """
        The GSIMs are equal if their TOML representations are equal
        """
        if self._toml:
            return self._toml == other._toml
        else:
            return str(self) == str(other)

    def __hash__(self):
        """
        We use the TOML representation as hash: it means that we can
        use equivalently GSIM instances or strings as dictionary keys.
        """
        return hash(self._toml) if self._toml else hash(str(self))

    def __repr__(self):
        """
        String representation for GSIM instances in TOML format.
        """
        if self._toml:
            return self._toml
        return '[%s]' % self.__class__.__name__


def check_sites(gsims, sitecol):
    """
    Raise a ValueError if some site has a vs30 outside the VS30_RANGE
    of a GSIM instantiated with vs30_strict=True, before starting the
    calculation.

    :param gsims: a list of GSIM instances
    :param sitecol: a :class:`openquake.hazardlib.site.SiteCollection`
    """
    for gsim in gsims:
        if not getattr(gsim, 'vs30_strict', False):
            continue
        vmin, vmax = gsim.VS30_RANGE
        vs30 = sitecol.vs30
        bad = (vs30 < vmin) | (vs30 > vmax)
        if bad.any():
            raise ValueError(
                f'{gsim.__class__.__name__} is calibrated for {vmin} <= '
                f'Vs30 <= {vmax} m/s, but {bad.sum()} site(s) have Vs30 '
                f'in the range [{vs30.min()}, {vs30.max()}]; fix the '
                'site model or set "strict = false" in the job.ini to '
                'clamp the out-of-range values')


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


class DummyGMPE(GMPE):
    """
    A fake GMPE doing nothing, to be used with zero-weight branches of
    the logic tree.
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {}
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.HORIZONTAL
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = {
        const.StdDev.TOTAL, const.StdDev.INTER_EVENT, const.StdDev.INTRA_EVENT}
    REQUIRES_SITES_PARAMETERS = set()
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}
    REQUIRES_DISTANCES = {'rrup'}

    def __init__(self, ordinal=0):
        self.ordinal = ordinal

    def compute(self, ctx: numpy.recarray, imts, mean, sig, tau, phi):
        sig[:] = .005
        tau[:] = .003
        phi[:] = .004
