# The Hazard Library
# Copyright (C) 2012-2014, GEM Foundation
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
Module :mod:`openquake.hazardlib.gsim.base` defines base classes for
different kinds of :class:`ground shaking intensity models
<GroundShakingIntensityModel>`.
"""
from __future__ import division

import abc
import math
import warnings
import functools
import contextlib
from copy import deepcopy

import h5py
import scipy.stats
from scipy.special import ndtr
from scipy.interpolate import interp1d
import numpy

from openquake.hazardlib import const
from openquake.hazardlib import imt as imt_module
from openquake.baselib.python3compat import with_metaclass


class NonInstantiableError(Exception):
    """
    Raised when a non instantiable GSIM is called
    """


class NotVerifiedWarning(UserWarning):
    """
    Raised when a non verified GSIM is instantiated
    """


# the builtin DeprecationWarning has been silenced in Python 2.7
class DeprecationWarning(UserWarning):
    """
    Raised the first time a deprecated function is called
    """


def deprecated(message):
    """
    Return a decorator to make deprecated functions.

    :param message:
        the message to print the first time the
        deprecated function is used.

    Here is an example of usage:

    >>> @deprecated('Use new_function instead')
    ... def old_function():
    ...     'Do something'
    """
    def _deprecated(func):
        func.called = False
        msg = '%s.%s has been deprecated. %s' % (
            func.__module__, func.__name__, message)

        @functools.wraps(func)
        def wrapper(*args, **kw):
            if not func.called:
                warnings.warn(msg, DeprecationWarning, stacklevel=2)
                func.called = True
            return func(*args, **kw)
        return wrapper
    return _deprecated


def gsim_imt_dt(sorted_gsims, sorted_imts):
    """
    Build a numpy dtype as a nested record with keys 'idx' and nested
    (gsim, imt).

    :param sorted_gsims: a list of GSIM instances, sorted lexicographically
    :param sorted_imts: a list of intensity measure type strings
    """
    imt_dt = numpy.dtype([(imt, float) for imt in sorted_imts])
    gsim_imt_dt = numpy.dtype(
        [('idx', numpy.uint32)] +
        [(str(gsim), imt_dt) for gsim in sorted_gsims])
    return gsim_imt_dt


class MetaGSIM(abc.ABCMeta):
    """
    Metaclass controlling the instantiation mechanism.  A subclass with
    instantiable=False will raise a NonInstantiableError when directly
    instantiated. A GroundShakingIntensityModel subclass with an
    attribute deprecated=True will print a deprecation warning when
    instantiated. A subclass with an attribute non_verified=True will
    print a UserWarning.
    """
    instantiable = True
    deprecated = False
    non_verified = False

    def __call__(cls, **kwargs):
        if not cls.instantiable:
            raise NonInstantiableError(
                '%s cannot be directly instantiated in this context' % cls)
        if cls.deprecated:
            msg = '%s is deprecated - use %s instead' % (
                cls.__name__, cls.__base__.__name__)
            warnings.warn(msg, DeprecationWarning)
        if cls.non_verified:
            msg = ('%s is not independently verified - the user is liable '
                   'for their application') % cls.__name__
            warnings.warn(msg, NotVerifiedWarning)
        self = super(MetaGSIM, cls).__call__(**kwargs)
        self.kwargs = kwargs
        return self

    # NB: the idea is to use this context manager inside the oqtask
    # decorator in the engine, so that GSIM classes cannot be directly
    # instantiated in the workers; however, they can still be
    # instantiated indirectly via __new__, so that unpickling works
    @contextlib.contextmanager
    def forbid_instantiation(cls):
        """
        Make the class and all its subclassed not directly instantiable
        """
        cls.instantiable = False
        try:
            yield
        finally:
            cls.instantiable = True


@functools.total_ordering
class GroundShakingIntensityModel(with_metaclass(MetaGSIM)):
    """
    Base class for all the ground shaking intensity models.

    A Ground Shaking Intensity Model (GSIM) defines a set of equations
    for computing mean and standard deviation of a Normal distribution
    representing the variability of an intensity measure (or of its logarithm)
    at a site given an earthquake rupture.

    This class is not intended to be subclassed directly, instead
    the actual GSIMs should subclass either :class:`GMPE` or :class:`IPE`.

    Subclasses of both must implement :meth:`get_mean_and_stddevs`
    and all the class attributes with names starting from ``DEFINED_FOR``
    and ``REQUIRES``.
    """

    #: Reference to a
    #: :class:`tectonic region type <openquake.hazardlib.const.TRT>` this GSIM
    #: is defined for. One GSIM can implement only one tectonic region type.
    DEFINED_FOR_TECTONIC_REGION_TYPE = abc.abstractproperty()

    #: Set of :mod:`intensity measure types <openquake.hazardlib.imt>`
    #this GSIM can
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
    #:     :meth:`~openquake.hazardlib.geo.surface.base.BaseQuadrilateralSurface.get_top_edge_depth`.
    #:
    #: These parameters are available from the :class:`RuptureContext` object
    #: attributes with same names.
    REQUIRES_RUPTURE_PARAMETERS = abc.abstractproperty()

    #: Set of types of distance measures between rupture and sites. Possible
    #: values are:
    #:
    #: ``rrup``
    #:     Closest distance to rupture surface.  See
    #:     :meth:`~openquake.hazardlib.geo.surface.base.BaseQuadrilateralSurface.get_min_distance`.
    #: ``rjb``
    #:     Distance to rupture's surface projection. See
    #:     :meth:`~openquake.hazardlib.geo.surface.base.BaseQuadrilateralSurface.get_joyner_boore_distance`.
    #: ``rx``
    #:     Perpendicular distance to rupture top edge projection.
    #:     See :meth:`~openquake.hazardlib.geo.surface.base.BaseQuadrilateralSurface.get_rx_distance`.
    #: ``ry0``
    #:     Horizontal distance off the end of the rupture measured parallel to
    #      strike. See:
    #:     See :meth:`~openquake.hazardlib.geo.surface.base.BaseQuadrilateralSurface.get_ry0_distance`.
    #: ``rcdpp``
    #:     Direct point parameter for directivity effect centered on the site- and earthquake-specific
    #      average DPP used. See:
    #:     See :meth:`~openquake.hazardlib.source.rupture.ParametricProbabilisticRupture.get_dppvalue`.
    #:
    #: All the distances are available from the :class:`DistancesContext`
    #: object attributes with same names. Values are in kilometers.
    REQUIRES_DISTANCES = abc.abstractproperty()

    @abc.abstractmethod
    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        Calculate and return mean value of intensity distribution and it's
        standard deviation.

        Method must be implemented by subclasses.

        :param sites:
            Instance of :class:`SitesContext` with parameters of sites
            collection assigned to respective values as numpy arrays.
            Only those attributes that are listed in class'
            :attr:`REQUIRES_SITES_PARAMETERS` set are available.
        :param rup:
            Instance of :class:`RuptureContext` with parameters of a rupture
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

    def get_poes(self, sctx, rctx, dctx, imt, imls, truncation_level):
        """
        Calculate and return probabilities of exceedance (PoEs) of one or more
        intensity measure levels (IMLs) of one intensity measure type (IMT)
        for one or more pairs "site -- rupture".

        :param sctx:
            An instance of :class:`SitesContext` with sites information
            to calculate PoEs on.
        :param rctx:
            An instance of :class:`RuptureContext` with a single rupture
            information.
        :param dctx:
            An instance of :class:`DistancesContext` with information about
            the distances between sites and a rupture.

            All three contexts (``sctx``, ``rctx`` and ``dctx``) must conform
            to each other. The easiest way to get them is to call
            :meth:`make_contexts`.
        :param imt:
            An intensity measure type object (that is, an instance of one
            of classes from :mod:`openquake.hazardlib.imt`).
        :param imls:
            List of interested intensity measure levels (of type ``imt``).
        :param truncation_level:
            Can be ``None``, which means that the distribution of intensity
            is treated as Gaussian distribution with possible values ranging
            from minus infinity to plus infinity.

            When set to zero, the mean intensity is treated as an exact
            value (standard deviation is not even computed for that case)
            and resulting array contains 0 in places where IMT is strictly
            lower than the mean value of intensity and 1.0 where IMT is equal
            or greater.

            When truncation level is positive number, the intensity
            distribution is processed as symmetric truncated Gaussian with
            range borders being ``mean - truncation_level * stddev`` and
            ``mean + truncation_level * stddev``. That is, the truncation
            level expresses how far the range borders are from the mean
            value and is defined in units of sigmas. The resulting PoEs
            for that mode are values of complementary cumulative distribution
            function of that truncated Gaussian applied to IMLs.

        :returns:
            A dictionary of the same structure as parameter ``imts`` (see
            above). Instead of lists of IMLs values of the dictionaries
            have 2d numpy arrays of corresponding PoEs, first dimension
            represents sites and the second represents IMLs.

        :raises ValueError:
            If truncation level is not ``None`` and neither non-negative
            float number, and if ``imts`` dictionary contain wrong or
            unsupported IMTs (see :attr:`DEFINED_FOR_INTENSITY_MEASURE_TYPES`).
        """
        if truncation_level is not None and truncation_level < 0:
            raise ValueError('truncation level must be zero, positive number '
                             'or None')
        self._check_imt(imt)

        if truncation_level == 0:
            # zero truncation mode, just compare imls to mean
            imls = self.to_distribution_values(imls)
            mean, _ = self.get_mean_and_stddevs(sctx, rctx, dctx, imt, [])
            mean = mean.reshape(mean.shape + (1, ))
            return (imls <= mean).astype(float)
        else:
            # use real normal distribution
            assert (const.StdDev.TOTAL
                    in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES)
            imls = self.to_distribution_values(imls)
            mean, [stddev] = self.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                       [const.StdDev.TOTAL])
            mean = mean.reshape(mean.shape + (1, ))
            stddev = stddev.reshape(stddev.shape + (1, ))
            values = (imls - mean) / stddev
            if truncation_level is None:
                return _norm_sf(values)
            else:
                return _truncnorm_sf(truncation_level, values)

    def disaggregate_poe(self, sctx, rctx, dctx, imt, iml,
                         truncation_level, n_epsilons):
        """
        Disaggregate (separate) PoE of ``iml`` in different contributions
        each coming from ``n_epsilons`` distribution bins.

        If ``truncation_level = 3``, ``n_epsilons = 3``, bin edges are
        ``-3 .. -1``, ``-1 .. +1`` and ``+1 .. +3``.

        :param n_epsilons:
            Integer number of bins to split truncated Gaussian distribution to.

        Other parameters are the same as for :meth:`get_poes`, with
        differences that ``iml`` is only one single intensity level
        and ``truncation_level`` is required to be positive.

        :returns:
            Contribution to probability of exceedance of ``iml`` coming
            from different sigma bands in a form of 1d numpy array with
            ``n_epsilons`` floats between 0 and 1.
        """
        if not truncation_level > 0:
            raise ValueError('truncation level must be positive')
        self._check_imt(imt)

        # compute mean and standard deviations
        mean, [stddev] = self.get_mean_and_stddevs(sctx, rctx, dctx, imt,
                                                   [const.StdDev.TOTAL])

        # compute iml value with respect to standard (mean=0, std=1)
        # normal distributions
        iml = self.to_distribution_values(iml)
        standard_imls = (iml - mean) / stddev

        distribution = scipy.stats.truncnorm(- truncation_level,
                                             truncation_level)
        epsilons = numpy.linspace(- truncation_level, truncation_level,
                                  n_epsilons + 1)
        # compute epsilon bins contributions
        contribution_by_bands = (distribution.cdf(epsilons[1:]) -
                                 distribution.cdf(epsilons[:-1]))

        # take the minimum epsilon larger than standard_iml
        iml_bin_indices = numpy.searchsorted(epsilons, standard_imls)

        return numpy.array([
            # take full disaggregated distribution for the case of
            # ``iml <= mean - truncation_level * stddev``
            contribution_by_bands
            if idx == 0 else

            # take zeros if ``iml >= mean + truncation_level * stddev``
            numpy.zeros(n_epsilons)
            if idx >= n_epsilons + 1 else

            # for other cases (when ``iml`` falls somewhere in the
            # histogram):
            numpy.concatenate((
                # take zeros for bins that are on the left hand side
                # from the bin ``iml`` falls into,
                numpy.zeros(idx - 1),
                # ... area of the portion of the bin containing ``iml``
                # (the portion is limited on the left hand side by
                # ``iml`` and on the right hand side by the bin edge),
                [distribution.sf(standard_imls[i])
                 - contribution_by_bands[idx:].sum()],
                # ... and all bins on the right go unchanged.
                contribution_by_bands[idx:]
            ))

            for i, idx in enumerate(iml_bin_indices)
        ])

    @abc.abstractmethod
    def to_distribution_values(self, values):
        """
        Convert a list or array of values in units of IMT to a numpy array
        of values of intensity measure distribution (like taking the natural
        logarithm for :class:`GMPE`).

        This method is implemented by both :class:`GMPE` and :class:`IPE`
        so there is no need to override it in actual GSIM implementations.
        """

    @abc.abstractmethod
    def to_imt_unit_values(self, values):
        """
        Convert a list or array of values of intensity measure distribution
        (like ones returned from :meth:`get_mean_and_stddevs`) to values
        in units of IMT. This is the opposite operation
        to :meth:`to_distribution_values`.

        This method is implemented by both :class:`GMPE` and :class:`IPE`
        so there is no need to override it in actual GSIM implementations.
        """

    def make_distances_context(self, site_collection, rupture):
        """
        Create distances context object for given site collection and rupture.

        :param site_collection:
            Instance of :class:`openquake.hazardlib.site.SiteCollection`.

        :param rupture:
            Instance of
            :class:`~openquake.hazardlib.source.rupture.Rupture` (or
            subclass of
            :class:
            `~openquake.hazardlib.source.rupture.BaseProbabilisticRupture`).

        :returns:
            Source to site distances as instance of :class:
            `DistancesContext()`. Only those  values that are required by GSIM
            are filled in this context.

        :raises ValueError:
            If any of declared required distance parameters is unknown.
        """
        dctx = DistancesContext()
        for param in self.REQUIRES_DISTANCES:
            if param == 'rrup':
                dist = rupture.surface.get_min_distance(site_collection.mesh)
            elif param == 'rx':
                dist = rupture.surface.get_rx_distance(site_collection.mesh)
            elif param == 'ry0':
                dist = rupture.surface.get_ry0_distance(site_collection.mesh)
            elif param == 'rjb':
                dist = rupture.surface.get_joyner_boore_distance(
                    site_collection.mesh
                )
            elif param == 'rhypo':
                dist = rupture.hypocenter.distance_to_mesh(
                    site_collection.mesh
                )
            elif param == 'repi':
                dist = rupture.hypocenter.distance_to_mesh(
                    site_collection.mesh, with_depths=False
                )
            elif param == 'rcdpp':
                dist = rupture.get_cdppvalue(site_collection.mesh)
            else:
                raise ValueError('%s requires unknown distance measure %r' %
                                 (type(self).__name__, param))
            setattr(dctx, param, dist)
        return dctx

    def make_sites_context(self, site_collection):
        """
        Create context objects for given site collection

        :param site_collection:
            Instance of :class:`openquake.hazardlib.site.SiteCollection`.

        :returns:
            Site parameters as instance of :class:
            `SitesContext()`. Only those  values that are required by GSIM
            are filled in this context.

        :raises ValueError:
            If any of declared required site parameters is unknown.

        """
        sctx = SitesContext()
        for param in self.REQUIRES_SITES_PARAMETERS:
            try:
                value = getattr(site_collection, param)
            except AttributeError:
                raise ValueError('%s requires unknown site parameter %r' %
                                 (type(self).__name__, param))
            setattr(sctx, param, value)
        return sctx

    def make_rupture_context(self, rupture):
        """
        Create context object for given rupture.

        :param rupture:
            Instance of
            :class:`~openquake.hazardlib.source.rupture.Rupture` (or
            subclass of
            :class:`~openquake.hazardlib.source.rupture.BaseProbabilisticRupture`).

        :returns:
            Rupture parameters as instance of :class:
            `RuptureContext()`. Only those  values that are required by GSIM
            are filled in this context.

        :raises ValueError:
            If any of declared required rupture parameters is unknown.
        """
        rctx = RuptureContext()
        for param in self.REQUIRES_RUPTURE_PARAMETERS:
            if param == 'mag':
                value = rupture.mag
            elif param == 'strike':
                value = rupture.surface.get_strike()
            elif param == 'dip':
                value = rupture.surface.get_dip()
            elif param == 'rake':
                value = rupture.rake
            elif param == 'ztor':
                value = rupture.surface.get_top_edge_depth()
            elif param == 'hypo_lon':
                value = rupture.hypocenter.longitude
            elif param == 'hypo_lat':
                value = rupture.hypocenter.latitude
            elif param == 'hypo_depth':
                value = rupture.hypocenter.depth
            elif param == 'width':
                value = rupture.surface.get_width()
            else:
                raise ValueError('%s requires unknown rupture parameter %r' %
                                 (type(self).__name__, param))
            setattr(rctx, param, value)
        return rctx

    def make_contexts(self, site_collection, rupture):
        """
        Create context objects for given site collection and rupture.

        :param site_collection:
            Instance of :class:`openquake.hazardlib.site.SiteCollection`.

        :param rupture:
            Instance of
            :class:`~openquake.hazardlib.source.rupture.Rupture` (or
            subclass of
            :class:`~openquake.hazardlib.source.rupture.BaseProbabilisticRupture`).

        :returns:
            Tuple of three items: sites context, rupture context and
            distances context, that is, instances of
            :class:`SitesContext`, :class:`RuptureContext` and
            :class:`DistancesContext` in a specified order. Only those
            values that are required by GSIM are filled in in
            contexts.

        :raises ValueError:
            If any of declared required parameters (that includes site, rupture
            and distance parameters) is unknown.
        """
        return (self.make_sites_context(site_collection),
                self.make_rupture_context(rupture),
                self.make_distances_context(site_collection, rupture))

    def _check_imt(self, imt):
        """
        Make sure that ``imt`` is valid and is supported by this GSIM.
        """
        if not issubclass(type(imt), imt_module._IMT):
            raise ValueError('imt must be an instance of IMT subclass')
        if not type(imt) in self.DEFINED_FOR_INTENSITY_MEASURE_TYPES:
            raise ValueError('imt %s is not supported by %s' %
                             (type(imt).__name__, type(self).__name__))

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
        return hash(str(self))

    def __str__(self):
        """
        To be overridden in subclasses if the GSIM takes parameters.
        """
        return self.__class__.__name__

    def __repr__(self):
        """
        Default string representation for GSIM instances. It contains
        the name and values of the arguments, if any.
        """
        # NB: ast.literal_eval(repr(gsim)) must work
        kwargs = ', '.join('%s=%r' % kv for kv in sorted(self.kwargs.items()))
        return repr("%s(%s)" % (self.__class__.__name__, kwargs))


def _truncnorm_sf(truncation_level, values):
    """
    Survival function for truncated normal distribution.

    Assumes zero mean, standard deviation equal to one and symmetric
    truncation.

    :param truncation_level:
        Positive float number representing the truncation on both sides
        around the mean, in units of sigma.
    :param values:
        Numpy array of values as input to a survival function for the given
        distribution.
    :returns:
        Numpy array of survival function results in a range between 0 and 1.

    >>> from scipy.stats import truncnorm
    >>> truncnorm(-3, 3).sf(0.12345) == _truncnorm_sf(3, 0.12345)
    True
    """
    # notation from http://en.wikipedia.org/wiki/Truncated_normal_distribution.
    # given that mu = 0 and sigma = 1, we have alpha = a and beta = b.

    # "CDF" in comments refers to cumulative distribution function
    # of non-truncated distribution with that mu and sigma values.

    # assume symmetric truncation, that is ``a = - truncation_level``
    # and ``b = + truncation_level``.

    # calculate CDF of b
    phi_b = ndtr(truncation_level)

    # calculate Z as ``Z = CDF(b) - CDF(a)``, here we assume that
    # ``CDF(a) == CDF(- truncation_level) == 1 - CDF(b)``
    z = phi_b * 2 - 1

    # calculate the result of survival function of ``values``,
    # and restrict it to the interval where probability is defined --
    # 0..1. here we use some transformations of the original formula
    # that is ``SF(x) = 1 - (CDF(x) - CDF(a)) / Z`` in order to minimize
    # number of arithmetic operations and function calls:
    # ``SF(x) = (Z - CDF(x) + CDF(a)) / Z``,
    # ``SF(x) = (CDF(b) - CDF(a) - CDF(x) + CDF(a)) / Z``,
    # ``SF(x) = (CDF(b) - CDF(x)) / Z``.
    return ((phi_b - ndtr(values)) / z).clip(0.0, 1.0)


def _norm_sf(values):
    """
    Survival function for normal distribution.

    Assumes zero mean and standard deviation equal to one.

    ``values`` parameter and the return value are the same
    as in :func:`_truncnorm_sf`.

    >>> from scipy.stats import norm
    >>> norm.sf(0.12345) == _norm_sf(0.12345)
    True
    """
    # survival function by definition is ``SF(x) = 1 - CDF(x)``,
    # which is equivalent to ``SF(x) = CDF(- x)``, since (given
    # that the normal distribution is symmetric with respect to 0)
    # the integral between ``[x, +infinity]`` (that is the survival
    # function) is equal to the integral between ``[-infinity, -x]``
    # (that is the CDF at ``- x``).
    return ndtr(- values)


class GMPE(GroundShakingIntensityModel):
    """
    Ground-Motion Prediction Equation is a subclass of generic
    :class:`GroundShakingIntensityModel` with a distinct feature
    that the intensity values are log-normally distributed.

    Method :meth:`~GroundShakingIntensityModel.get_mean_and_stddevs`
    of actual GMPE implementations is supposed to return the mean
    value as a natural logarithm of intensity.
    """
    def to_distribution_values(self, values):
        """
        Returns numpy array of natural logarithms of ``values``.
        """
        return numpy.log(values)

    def to_imt_unit_values(self, values):
        """
        Returns numpy array of exponents of ``values``.
        """
        return numpy.exp(values)


class IPE(GroundShakingIntensityModel):
    """
    Intensity Prediction Equation is a subclass of generic
    :class:`GroundShakingIntensityModel` which is suitable for
    intensity measures that are normally distributed. In particular,
    for :class:`~openquake.hazardlib.imt.MMI`.
    """
    def to_distribution_values(self, values):
        """
        Returns numpy array of ``values`` without any conversion.
        """
        return numpy.array(values, dtype=float)

    def to_imt_unit_values(self, values):
        """
        Returns numpy array of ``values`` without any conversion.
        """
        return numpy.array(values, dtype=float)


class BaseContext(with_metaclass(abc.ABCMeta)):
    """
    Base class for context object.
    """

    def __eq__(self, other):
        """
        Return True if ``other`` has same attributes with same values.
        """
        if isinstance(other, self.__class__):
            if self.__slots__ == other.__slots__:
                self_other = [
                    numpy.all(
                        getattr(self, s, None) == getattr(other, s, None)
                    )
                    for s in self.__slots__
                ]
                return numpy.all(self_other)

        return False


class SitesContext(BaseContext):
    """
    Sites calculation context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are
    intended to represent relevant features of the sites collection.
    Every GSIM class is required to declare what :attr:`sites parameters
    <GroundShakingIntensityModel.REQUIRES_SITES_PARAMETERS>` does it need.
    Only those required parameters are made available in a result context
    object.
    """
    __slots__ = ('vs30', 'vs30measured', 'z1pt0', 'z2pt5', 'backarc',
        'lons', 'lats')


class DistancesContext(BaseContext):
    """
    Distances context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are
    intended to represent relevant distances between sites from the collection
    and the rupture. Every GSIM class is required to declare what
    :attr:`distance measures <GroundShakingIntensityModel.REQUIRES_DISTANCES>`
    does it need. Only those required values are calculated and made available
    in a result context object.
    """
    __slots__ = ('rrup', 'rx', 'rjb', 'rhypo', 'repi', 'ry0', 'rcdpp')


class RuptureContext(BaseContext):
    """
    Rupture calculation context for ground shaking intensity models.

    Instances of this class are passed into
    :meth:`GroundShakingIntensityModel.get_mean_and_stddevs`. They are
    intended to represent relevant features of a single rupture. Every
    GSIM class is required to declare what :attr:`rupture parameters
    <GroundShakingIntensityModel.REQUIRES_RUPTURE_PARAMETERS>` does it need.
    Only those required parameters are made available in a result context
    object.
    """
    __slots__ = (
        'mag', 'strike', 'dip', 'rake', 'ztor', 'hypo_lon', 'hypo_lat',
        'hypo_depth', 'width', 'hypo_loc'
    )


class CoeffsTable(object):
    r"""
    Instances of :class:`CoeffsTable` encapsulate tables of coefficients
    corresponding to different IMTs.

    Tables are defined in a space-separated tabular form in a simple string
    literal (heading and trailing whitespace does not matter). The first column
    in the table must be named "IMT" (or "imt") and thus should represent IMTs:

    >>> CoeffsTable(table='''imf z
    ...                      pga 1''')
    Traceback (most recent call last):
        ...
    ValueError: first column in a table must be IMT

    Names of other columns are used as coefficients dicts keys. The values
    in the first column should correspond to real intensity measure types,
    see :mod:`openquake.hazardlib.imt`:

    >>> CoeffsTable(table='''imt  z
    ...                      pgx  2''')
    Traceback (most recent call last):
        ...
    ValueError: unknown IMT 'PGX'

    Note that :class:`CoeffsTable` only accepts keyword argumets:

    >>> CoeffsTable()
    Traceback (most recent call last):
        ...
    TypeError: CoeffsTable requires "table" kwarg
    >>> CoeffsTable(table='', foo=1)
    Traceback (most recent call last):
        ...
    TypeError: CoeffsTable got unexpected kwargs: {'foo': 1}

    If there are :class:`~openquake.hazardlib.imt.SA` IMTs in the table, they
    are not referenced by name, because they require parametrization:

    >>> CoeffsTable(table='''imt  x
    ...                      sa   15''')
    Traceback (most recent call last):
        ...
    ValueError: specify period as float value to declare SA IMT
    >>> CoeffsTable(table='''imt  x
    ...                      0.1  20''')
    Traceback (most recent call last):
        ...
    TypeError: attribute "sa_damping" is required for tables defining SA

    So proper table defining SA looks like this:

    >>> ct = CoeffsTable(sa_damping=5, table='''
    ...     imt   a    b     c   d
    ...     pga   1    2.4  -5   0.01
    ...     pgd  7.6  12     0  44.1
    ...     0.1  10   20    30  40
    ...     1.0   1    2     3   4
    ...     10    2    4     6   8
    ... ''')

    Table objects could be indexed by IMT objects (this returns a dictionary
    of coefficients):

    >>> from openquake.hazardlib import imt
    >>> ct[imt.PGA()] == dict(a=1, b=2.4, c=-5, d=0.01)
    True
    >>> ct[imt.PGD()] == dict(a=7.6, b=12, c=0, d=44.1)
    True
    >>> ct[imt.SA(damping=5, period=0.1)] == dict(a=10, b=20, c=30, d=40)
    True
    >>> ct[imt.PGV()]
    Traceback (most recent call last):
        ...
    KeyError: PGV()
    >>> ct[imt.SA(1.0, 4)]
    Traceback (most recent call last):
        ...
    KeyError: SA(period=1.0, damping=4)

    Table of coefficients for spectral acceleration could be indexed
    by instances of :class:`openquake.hazardlib.imt.SA` with period
    value that is not specified in the table. The coefficients then
    get interpolated between the ones for closest higher and closest
    lower period. That scaling of coefficients works in a logarithmic
    scale of periods and only within the same damping:

    >>> '%.5f' % ct[imt.SA(period=0.2, damping=5)]['a']
    '7.29073'
    >>> '%.5f' % ct[imt.SA(period=0.9, damping=5)]['c']
    '4.23545'
    >>> '%.5f' % ct[imt.SA(period=5, damping=5)]['c']
    '5.09691'
    >>> ct[imt.SA(period=0.9, damping=15)]
    Traceback (most recent call last):
        ...
    KeyError: SA(period=0.9, damping=15)

    Extrapolation is not possible:

    >>> ct[imt.SA(period=0.01, damping=5)]
    Traceback (most recent call last):
        ...
    KeyError: SA(period=0.01, damping=5)
    """
    def __init__(self, **kwargs):
        if not 'table' in kwargs:
            raise TypeError('CoeffsTable requires "table" kwarg')
        table = kwargs.pop('table').strip().splitlines()
        sa_damping = kwargs.pop('sa_damping', None)
        if kwargs:
            raise TypeError('CoeffsTable got unexpected kwargs: %r' % kwargs)
        header = table.pop(0).split()
        if not header[0].upper() == "IMT":
            raise ValueError('first column in a table must be IMT')
        coeff_names = header[1:]
        self.sa_coeffs = {}
        self.non_sa_coeffs = {}
        for row in table:
            row = row.split()
            imt_name = row[0].upper()
            if imt_name == 'SA':
                raise ValueError('specify period as float value '
                                 'to declare SA IMT')
            imt_coeffs = dict(zip(coeff_names, map(float, row[1:])))
            try:
                sa_period = float(imt_name)
            except:
                if not hasattr(imt_module, imt_name):
                    raise ValueError('unknown IMT %r' % imt_name)
                imt = getattr(imt_module, imt_name)()
                self.non_sa_coeffs[imt] = imt_coeffs
            else:
                if sa_damping is None:
                    raise TypeError('attribute "sa_damping" is required '
                                    'for tables defining SA')
                imt = imt_module.SA(sa_period, sa_damping)
                self.sa_coeffs[imt] = imt_coeffs

    def __getitem__(self, imt):
        """
        Return a dictionary of coefficients corresponding to ``imt``
        from this table (if there is a line for requested IMT in it),
        or the dictionary of interpolated coefficients, if ``imt`` is
        of type :class:`~openquake.hazardlib.imt.SA` and interpolation
        is possible.

        :raises KeyError:
            If ``imt`` is not available in the table and no interpolation
            can be done.
        """
        if not isinstance(imt, imt_module.SA):
            return self.non_sa_coeffs[imt]

        try:
            return self.sa_coeffs[imt]
        except KeyError:
            pass

        max_below = min_above = None
        for unscaled_imt in list(self.sa_coeffs):
            if unscaled_imt.damping != imt.damping:
                continue
            if unscaled_imt.period > imt.period:
                if min_above is None or unscaled_imt.period < min_above.period:
                    min_above = unscaled_imt
            elif unscaled_imt.period < imt.period:
                if max_below is None or unscaled_imt.period > max_below.period:
                    max_below = unscaled_imt
        if max_below is None or min_above is None:
            raise KeyError(imt)

        # ratio tends to 1 when target period tends to a minimum
        # known period above and to 0 if target period is close
        # to maximum period below.
        ratio = ((math.log(imt.period) - math.log(max_below.period))
                 / (math.log(min_above.period) - math.log(max_below.period)))
        max_below = self.sa_coeffs[max_below]
        min_above = self.sa_coeffs[min_above]
        return dict(
            (co, (min_above[co] - max_below[co]) * ratio + max_below[co])
            for co in max_below
        )

def hdf_arrays_to_dict(hdfgroup):
    """
    Convert an hdf5 group containins only data sets to a dictionary of
    data sets
    :param hdfgroup:
        Instance of :class: h5py.Group
    :returns:
        Dictionary containing each of the datasets within the group arranged
        by name
    """
    return dict([(key, hdfgroup[key][:]) for key in hdfgroup.keys()])


class AmplificationTable(object):
    """
    Class to apply amplification from the GMPE tables.

    :param shape:
        Shape of the amplification arrays as a tuple of (Number Distances,
        Number IMTs, Number Magnitudes, Number Amplification Levels)
    :param periods:
        Spectral periods defined in table
    :param mean:
        Amplification factors for the mean ground motion
    :param sigma:
        List of modification factors for the standard deviation of ground
        motion
    :param magnitudes:
        Magnitude values for the tables
    :param distances:
        Distance values for the tables
    :param parameter:
        Parameter to which the amplification applies. Must be an element
        inside the __slots__ defines in the :class: openquake.hazardlib.
        gsim.base.RuptureContext or the :class: openquake.hazardlib.gsim.base.
        SitesContext
    :param values:
        Array of values to which each amplification table corresponds
    :param element:
        Indicates if the amplification corresponds to a rupture attribute or
        a site attribute
    """
    def __init__(self, amplification_group, magnitudes, distances):
        """
        Setup the amplification factors.

        :param amplification_group:
            Amplification model as instance of :class: h5py.Group
        :param magnitudes:
            Array of magnitudes
        :param distances:
            Array of distances
        """
        self.shape = None
        self.periods = None
        self.mean = None
        self.sigma = None
        self.magnitudes = magnitudes
        self.distances = distances
        self.parameter = amplification_group.attrs["apply_to"]
        self.values = numpy.array([float(key)
                                   for key in amplification_group.keys()])
        self.argidx = numpy.argsort(self.values)
        self.values = self.values[self.argidx]
        if self.parameter in RuptureContext.__slots__:
            self.element = "Rupture"
        elif self.parameter in SitesContext.__slots__:
            self.element = "Sites"
        else:
            raise ValueError("Amplification parameter %s not recognised!"
                             % self.parameter)
        self._build_data(amplification_group)

    def _build_data(self, amplification_group):
        """
        Creates the numpy array tables from the hdf5 tables
        """
        # Determine shape of the tables
        n_levels = len(amplification_group)
        n_d, n_p, n_m = amplification_group.items()[0][1]["IMLs/SA"].shape
        assert (n_d == len(self.distances)) and (n_m == len(self.magnitudes))
        # Instantiate the arrays with ones
        self.mean = {"SA": numpy.ones([n_d, n_p, n_m, n_levels]),
                     "PGA": numpy.ones([n_d, 1, n_m, n_levels]),
                     "PGV": numpy.ones([n_d, 1, n_m, n_levels])}
        self.sigma = {}
        for stddev_type in [const.StdDev.TOTAL, const.StdDev.INTER_EVENT,
                            const.StdDev.INTRA_EVENT]:
            if stddev_type in amplification_group.items()[0][1].keys():
                self.sigma[stddev_type] = deepcopy(self.mean)

        for iloc, (level, amp_model) in enumerate(amplification_group.items()):
            if "SA" in amp_model["IMLs"].keys():
                if iloc == 0:
                    self.periods = amp_model["IMLs/T"][:]
                else:
                    assert numpy.allclose(self.periods, amp_model["IMLs/T"][:])
            for imt in ["SA", "PGA", "PGV"]:
                if imt in amp_model["IMLs"].keys():
                    self.mean[imt][:, :, :, self.argidx[iloc]] =\
                        amp_model["IMLs/" + imt][:]
                    for stddev_type in self.sigma.keys():
                        self.sigma[stddev_type][imt]\
                            [:, :, :, self.argidx[iloc]] =\
                            amp_model["/".join([stddev_type, imt])][:]
        self.shape = (n_d, n_p, n_m, n_levels)

    def get_set(self):
        """
        Return the parameter as an instance a Python set
        """
        return set((self.parameter,))

    def get_amplification_factors(self, imt, sctx, rctx, dists, stddev_types):
        """
        Returns the amplification factors for the given rupture and site
        conditions.

        :param imt:
            Intensity measure type as an instance of the :class:
            openquake.hazardlib.imt
        :param sctx:
            Site parameters as instance of the :class:
            openquake.hazardlib.gsim.base.SitesContext
        :param rctx:
            Rupture parameters as instance of the :class:
            openquake.hazardlib.gsim.base.RuptureContext
        :param dists:
            Source to site distances (km)
        :param stddev_types:
            List of required standard deviation types
        :returns:
            * mean_amp - Amplification factors applied to the median ground
                         motion
            * sigma_amps - List of modification factors applied to the
                         standard deviations of ground motion
        """
        dist_level_table = self.get_mean_table(imt, rctx)
        sigma_tables = self.get_sigma_tables(imt, rctx, stddev_types)
        mean_interpolator = interp1d(self.values,
                                     numpy.log10(dist_level_table),
                                     axis=1)
        sigma_interpolators = [interp1d(self.values, sigma_table, axis=1)
                               for sigma_table in sigma_tables]
        if self.element == "Rupture":
            mean_amp = 10.0 ** mean_interpolator(
                getattr(rctx, self.parameter))[0] * numpy.ones_like(dists)
            sigma_amps = []
            for sig_interpolator in sigma_interpolators:
                sigma_amps.append(sig_interpolator(
                    getattr(rctx, self.parameter))[0] * numpy.ones_like(dists))
        else:
            mean_amp = 10.0 ** mean_interpolator(
                getattr(sctx, self.parameter))[0, :]
            sigma_amps = []
            for sig_interpolator in sigma_interpolators:
                sigma_amps.append(sig_interpolator(
                    getattr(sctx, self.parameter))[0, :] *
                    numpy.ones_like(dists))
        return mean_amp, sigma_amps

    def get_mean_table(self, imt, rctx):
        """
        Returns amplification factors for the mean, given the rupture and
        intensity measure type.

        :returns:
            amplification table as an array of [Number Distances,
            Number Levels]
        """
        # Levels by Distances
        if isinstance(imt, (imt_module.PGA, imt_module.PGV)):
            interpolator = interp1d(self.magnitudes,
                                    numpy.log10(self.mean[str(imt)]), axis=2)
            output_table = 10.0 ** (
                interpolator(rctx.mag).reshape(self.shape[0], self.shape[3])
                )
        else:
            # For spectral accelerations - need two step process
            # Interpolate period - log-log space
            interpolator = interp1d(numpy.log10(self.periods),
                                    numpy.log10(self.mean["SA"]),
                                    axis=1)
            period_table = interpolator(numpy.log10(imt.period))
            # Interpolate magnitude - linear-log space
            mag_interpolator = interp1d(self.magnitudes, period_table, axis=1)
            output_table = 10.0 ** (mag_interpolator(rctx.mag))
        return output_table

    def get_sigma_tables(self, imt, rctx, stddev_types):
        """
        Returns modification factors for the standard deviations, given the
        rupture and intensity measure type.

        :returns:
            List of standard deviation modification tables, each as an array
            of [Number Distances, Number Levels]

        """
        output_tables = []
        for stddev_type in stddev_types:
            # For PGA and PGV only needs to apply magnitude interpolation
            if isinstance(imt, (imt_module.PGA, imt_module.PGV)):
                interpolator = interp1d(self.magnitudes,
                                        self.sigma[stddev_type][str(imt)],
                                        axis=2)
                output_tables.append(
                    interpolator(rctx.mag).reshape(self.shape[0],
                                                   self.shape[3]))

            else:
                # For spectral accelerations - need two step process
                # Interpolate period
                interpolator = interp1d(numpy.log10(self.periods),
                                        self.sigma[stddev_type]["SA"],
                                        axis=1)
                period_table = interpolator(numpy.log10(imt.period))
                mag_interpolator = interp1d(self.magnitudes,
                                            period_table,
                                            axis=1)
                output_tables.append(mag_interpolator(rctx.mag))
        return output_tables


class GMPETable(GMPE):
    """
    Implements ground motion prediction equations in the form of a table from
    which the expected ground motion intensity levels and standard deviations
    are interpolated.

    In a GMPE tables the expected ground motions for each of the IMTs over the
    range of magnitudes and distances are stored in an hdf5 file on the path
    specified by the user.

    In this version of the GMPE the expected values are interpolated to the
    required IMT, magnitude and distance in three stages.

    i) Initially the correct IMT values are identified, interpolating in
       log-T|log-IML space between neighbouring spectral periods.

    ii) The IML values are then interpolated to the correct magnitude using
        linear-M|log-IML space

    iii) The IML values are then interpolated to the correct distance via
         linear-D|linear-IML interpolation
    """
    DEFINED_FOR_TECTONIC_REGION_TYPE = ""

    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set(())

    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = ""

    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set((const.StdDev.TOTAL,))

    REQUIRES_SITES_PARAMETERS = set(())

    REQUIRES_DISTANCES = set(())

    REQUIRES_RUPTURE_PARAMETERS = set(("mag",))

    GMPE_TABLE = None

    def __init__(self, gmpe_table=None):
        """
        Instantiate - either with a GMPE table or otherwise it will take
        the GMPE table defined
        """
        if not self.GMPE_TABLE:
            if gmpe_table:
                self.GMPE_TABLE = gmpe_table
            else:
                raise IOError("GMPE Table Not Defined!")
        super(GMPETable, self).__init__()
        self.imls = None
        self.stddevs = {}
        self.m_w = None
        self.distances = None
        self.distance_type = None
        self.amplification = None
        self._run_setup()

    def _run_setup(self):
        """
        Executes the preprocessing steps at the instantiation stage to read in
        the tables from hdf5 and hold them in memory.
        """
        fle = h5py.File(self.GMPE_TABLE, "r")
        self.distance_type = fle["Distances"].attrs["metric"]
        self.REQUIRES_DISTANCES.clear()
        self.REQUIRES_DISTANCES.update(set((self.distance_type,)))
        # Load in magnitude
        self.m_w = fle["Mw"][:]
        # Load in distances
        self.distances = fle["Distances"][:]
        # Load intensity measure types and levels
        self.imls = hdf_arrays_to_dict(fle["IMLs"])
        self._update_supported_imts()
        if "SA" in self.imls.keys() and not "T" in self.imls.keys():
            raise ValueError("Spectral Acceleration must be accompanied by "
                             "periods")
        # Get the standard deviations
        self._setup_standard_deviations(fle)
        if "Amplification" in fle.keys():
            self._setup_amplification(fle)
        fle.close()

    def _setup_standard_deviations(self, fle):
        """
        Reads the standard deviation tables from hdf5 and stores them in
        memory
        :param fle:
            HDF5 Tables as instance of :class: `h5py.File`
        """
        # Load in total standard deviation
        self.stddevs[const.StdDev.TOTAL] = hdf_arrays_to_dict(fle["Total"])
        # If other standard deviations
        for stddev_type in [const.StdDev.INTER_EVENT,
                            const.StdDev.INTRA_EVENT]:
            if stddev_type in fle.keys():
                self.stddevs[stddev_type] = hdf_arrays_to_dict(
                    fle[stddev_type])
                self.DEFINED_FOR_STANDARD_DEVIATION_TYPES.update(
                    set((stddev_type,)))

    def _setup_amplification(self, fle):
        """
        If amplification data is specified then reads into memory and updates
        the required rupture and site parameters
        """
        self.amplification = AmplificationTable(fle["Amplification"],
                                                self.m_w,
                                                self.distances)
        if self.amplification.element == "Sites":
            self.REQUIRES_SITES_PARAMETERS = set(())
            self.REQUIRES_SITES_PARAMETERS.update(
                set((self.amplification.parameter,)))
        elif self.amplification.element == "Rupture":
            # Re-set the site parameters
            self.REQUIRES_SITES_PARAMETERS = set(())
            self.REQUIRES_RUPTURE_PARAMETERS.update(
                set((self.amplification.parameter,)))

    def _update_supported_imts(self):
        """
        Updates the list of supported IMTs from the tables
        """
        imt_list = []
        for key in self.imls.keys():
            if "SA" in key:
                imt_list.append(imt_module.SA)
            elif key == "T":
                continue
            else:
                try:
                    imt_val = imt_module.from_string(key)
                except:
                    continue
                imt_list.append(imt_val.__class__)
        self.DEFINED_FOR_INTENSITY_MEASURE_TYPES.update(set(imt_list))

    def get_mean_and_stddevs(self, sctx, rctx, dctx, imt, stddev_types):
        """
        Returns the mean and standard deviations
        """
        # Return Distance Tables
        imls = self._return_tables(rctx.mag, imt, "IMLs")
        # Get distance vector for the given magnitude
        idx = numpy.searchsorted(self.m_w, rctx.mag)
        dists = self.distances[:, 0, idx - 1]
        # Get mean and standard deviations
        mean = self._get_mean(imls, dctx, dists)
        stddevs = self._get_stddevs(dists, rctx.mag, dctx, imt, stddev_types)
        if self.amplification:
            # Apply amplification
            mean_amp, sigma_amp = self.amplification.get_amplification_factors(
                imt,
                sctx,
                rctx,
                getattr(dctx, self.distance_type),
                stddev_types)
            mean = numpy.log(mean) + numpy.log(mean_amp)
            for iloc in range(len(stddev_types)):
                stddevs[iloc] *= sigma_amp[iloc]
            return mean, stddevs
        else:
            return numpy.log(mean), stddevs

    def _get_mean(self, data, dctx, dists):
        """
        Returns the mean intensity measure level from the tables
        :param data:
            The intensity measure level vector for the given magnitude and IMT
        :param key:
            The distance type
        :param distances:
            The distance vector for the given magnitude and IMT
        """
        interpolator_mean = interp1d(dists, data,
                                     bounds_error=False,
                                     fill_value=-999.)
        mean = interpolator_mean(getattr(dctx, self.distance_type))
        # For those distances less than or equal to the shortest distance
        # extrapolate the shortest distance value
        mean[getattr(dctx, self.distance_type) < (dists[0] + 1.0E-3)] = data[0]
        # For those distances significantly greater than the furthest distance
        # set to 1E-20.
        mean[getattr(dctx, self.distance_type) > (dists[-1] + 1.0E-3)] = 1E-20
        # If any distance is between the final distance and a margin of 0.001
        # km then assign to smallest distance
        mean[mean < -1.] = data[-1]
        return mean

    def _get_stddevs(self, dists, mag, dctx, imt, stddev_types):
        """
        Returns the total standard deviation of the intensity measure level
        from the tables.

        :param fle:
            HDF5 data stream as instance of :class: h5py.File
        :param distances:
            The distance vector for the given magnitude and IMT
        :param key:
            The distance type
        :param mag:
            The rupture magnitude
        """
        stddevs = []
        for stddev_type in stddev_types:
            if not stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES:
                raise ValueError("Standard Deviation type %s not supported"
                                 % stddev_type)
            sigma = self._return_tables(mag, imt, stddev_type)
            interpolator_std = interp1d(dists, sigma,
                                        bounds_error=False)
            stddev = interpolator_std(getattr(dctx, self.distance_type))
            stddev[getattr(dctx, self.distance_type) < dists[0]] = sigma[0]
            stddev[getattr(dctx, self.distance_type) > dists[-1]] = sigma[-1]
            stddevs.append(stddev)
        return stddevs

    def _return_tables(self, mag, imt, val_type):
        """
        Returns the vector of ground motions or standard deviations
        corresponding to the specific magnitude and intensity measure type.

        :param val_type:
            String indicating the type of data {"IMLs", "Total", "Inter" etc}
        """
        if isinstance(imt, (imt_module.PGA, imt_module.PGV)):
            # Get scalar imt
            if val_type == "IMLs":
                iml_table = self.imls[str(imt)][:]
            else:
                iml_table = self.stddevs[val_type][str(imt)][:]
            n_d, n_s, n_m = iml_table.shape
            iml_table = iml_table.reshape([n_d, n_m])
        else:
            if val_type == "IMLs":
                periods = self.imls["T"][:]
                iml_table = self.imls["SA"][:]
            else:
                periods = self.stddevs[val_type]["T"][:]
                iml_table = self.stddevs[val_type]["SA"][:]

            low_period = round(periods[0], 7)
            high_period = round(periods[-1], 7)

            if imt.period < low_period or imt.period > high_period:
                raise ValueError("Spectral period %.3f outside of valid range "
                                 "(%.3f to %.3f)" % (imt.period, periods[0],
                                                     periods[-1]))
            # Apply log-log interpolation for spectral period
            interpolator = interp1d(numpy.log10(periods),
                                    numpy.log10(iml_table),
                                    axis=1)
            iml_table = 10. ** interpolator(numpy.log10(imt.period))
        return self.apply_magnitude_interpolation(mag, iml_table)

    def apply_magnitude_interpolation(self, mag, iml_table):
        """
        Interpolates the tables to the required magnitude level

        :param float mag:
            Magnitude
        :param iml_table:
            Intensity measure level table
        """
        # Get magnitude values
        m_idx = numpy.searchsorted(self.m_w, mag)
        if mag < self.m_w[0] or mag > self.m_w[-1]:
            raise ValueError("Magnitude %.2f outside of supported range "
                             "(%.2f to %.2f)" % (mag,
                                                 self.m_w[0],
                                                 self.m_w[-1]))
        # It is assumed that log10 of the spectral acceleration scales
        # linearly (or approximately linearly) with magnitude
        m_interpolator = interp1d(self.m_w, numpy.log10(iml_table), axis=1)
        return 10.0 ** m_interpolator(mag)
