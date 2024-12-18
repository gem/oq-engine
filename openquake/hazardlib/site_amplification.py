# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2020, GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import numpy
from scipy.stats import norm
import pandas as pd

from openquake.baselib import hdf5
from openquake.hazardlib.stats import norm_cdf, truncnorm_sf
from openquake.hazardlib.site import ampcode_dt
from openquake.hazardlib.imt import from_string
from openquake.commonlib.oqvalidation import check_same_levels


class AmplFunction():
    """
    Class for managing an amplification function DataFrame.

    :param df:
        A :class:`pandas.DataFrame` instance
    :param soil:
        A string with the code of the site to be used
    """

    def __init__(self, df, soil=None):
        # If the function is used only for one soil type, then we filter out
        # the other soil typologies
        if soil is not None:
            df = df[df['ampcode'] == soil]
        if 'from_mag' in df.keys():
            self.mags = numpy.unique(df['from_mag'])
        self.df = df

    @classmethod
    def from_dframe(cls, df, soil=None):
        """
        :param df:
            A :class:`pandas.DataFrame` instance
        :param soil:
            A string
        :returns:
            A :class:`openquake.hazardlib.site_amplification.AmplFunction`
            instance
        """
        # Get IMTs for keys ampcode, from_mag, from_rrup, level, PGA, sigma_PGA
        imts = [key for key in df.keys() if key.startswith(('PGA', 'SA'))]

        # Create the temporary list of lists
        out = []
        for _, row in df.reset_index().iterrows():
            for imt in imts:
                out.append([row['ampcode'], row['from_mag'], row['from_rrup'],
                            row['level'], imt, row[imt], row['sigma_' + imt]])

        # Create the dataframe
        dtypes = {'ampcode': ampcode_dt, 'from_mag': float,
                  'from_rrup': float, 'level': float, 'imt': str,
                  'median': float, 'std': float}
        df = pd.DataFrame(out, columns=dtypes).astype(dtypes)
        return AmplFunction(df, soil)  # requires reset_index

    @classmethod
    def read_df(cls, csvfname):
        """
        :param csvfname: CSV file name
        :returns: a pandas DataFrame
        """
        df = hdf5.read_csv(csvfname, {'ampcode': ampcode_dt, None: float},
                           index='ampcode')
        df.fname = csvfname
        return df

    def get_mean_std(self, site, imt, iml, mags, dsts):
        """
        :param site:
            A string specifying the site
        :param imt:
            A string specifying the intensity measure type e.g. 'PGA' or
            'SA(1.0)'
        :param iml:
            A float with the shaking level on rock for which we need the
            amplification factor
        :param mags:
            An array of rupture magnitudes
        :param dst:
            An array of rupture-site distances
        :returns:
            A tuple with the median amplification factor and the std of the
            logarithm
        """
        df = self.df
        df = df[(df['ampcode'] == site) & (df['imt'] == imt)]
        tmp_dsts = numpy.array(sorted(df['from_rrup']))

        median = numpy.zeros(len(mags))
        std = numpy.zeros(len(mags))

        # TODO: figure out a way to do the following better
        for i, (mag, dst) in enumerate(zip(mags, dsts)):

            # Filtering magnitude
            idx = numpy.argmin((self.mags - mag) > 0)
            d = df[df['from_mag'] == self.mags[idx]]

            # Filtering distance
            idx = numpy.argmin((tmp_dsts - dst) > 0)
            d = d[d['from_rrup'] == tmp_dsts[idx]]

            # Interpolating
            median[i] = numpy.interp(iml, d['level'], d['median'])
            std[i] = numpy.interp(iml, d['level'], d['std'])

        return median, std

    def get_max_sigma(self):
        """
        :returns:
            The maximum sigma value in the amplification function
        """
        return max(self.df['std'])


def check_unique(df, kfields, fname):
    """
    Check if there are duplicate records with the respect to the
    composite primary key defined by the kfields
    """
    for k, rows in df.groupby(kfields):
        if len(rows) > 1:
            msg = 'Found duplicates for %s' % str(k)
            if fname:
                msg = '%s: %s' % (fname, msg)
            raise ValueError(msg)


class Amplifier(object):
    """
    Amplification class with methods .amplify and .amplify_gmfs.

    :param imtls:
        Intensity measure types and levels DictArray M x I
    :param ampl_df:
        A DataFrame containing amplification functions.
    :param amplevels:
        Intensity levels used for the amplified curves (if None, use the
        levels from the imtls dictionary). It's an array.
    """
    def __init__(self, imtls, ampl_df, amplevels=None):
        # Check input
        if not imtls:
            raise ValueError('There are no intensity_measure_types!')
        # If available, get the filename containing the amplification function
        fname = getattr(ampl_df, 'fname', None)
        # Set the intensity measure types and levels on rock
        self.imtls = imtls
        # Set the intensity levels for which we compute poes on soil. Note
        # that we assume they are the same for all the intensity measure types
        # considered
        self.amplevels = amplevels
        # This is the reference Vs30 for the amplification function
        self.vs30_ref = ampl_df.vs30_ref
        has_levels = 'level' in ampl_df.columns
        has_mags = 'from_mag' in ampl_df.columns
        # Checking the input dataframe. The first case is for amplification
        # functions that depend on magnitude, distance and iml (the latter
        # in this case can be probably removed since is closely correlated
        # to the other two variables
        if has_levels and 'from_mag' in ampl_df.keys():
            keys = ['ampcode', 'level', 'from_mag', 'from_rrup']
            check_unique(ampl_df, keys, fname)
        elif has_levels and 'level' in ampl_df.keys():
            check_unique(ampl_df, ['ampcode', 'level'], fname)
        else:
            check_unique(ampl_df, ['ampcode'], fname)
        missing = set(imtls) - set(ampl_df.columns[has_levels:])
        # Raise an error in case the hazard on rock does not contain
        # all the IMTs included in the amplification function
        if missing:
            raise ValueError('The amplification table does not contain %s'
                             % missing)
        if amplevels is None:  # for event based
            self.periods = [from_string(imt).period for imt in imtls]
        else:
            self.periods, levels = check_same_levels(imtls)
        # Create a dictionary containing for each site-category [key] a
        # dataframe [value] with the corresponding amplification function
        self.coeff = {}  # code -> dataframe
        self.ampcodes = []
        # This is a list with the names of the columns we will use to filter
        # the dataframe with the amplification function
        cols = list(imtls)
        if has_mags:
            cols.extend(['from_mag', 'from_rrup'])
        if has_levels:
            cols.append('level')
        # Appending to the list, the column names for sigma
        for col in ampl_df.columns:
            if col.startswith('sigma_'):
                cols.append(col)
        # Now we populate the dictionary containing for each site class the
        # corresponding dataframe with the amplification
        for code, df in ampl_df.groupby('ampcode'):
            self.ampcodes.append(code)
            if has_levels:
                self.coeff[code] = df[cols].set_index('level')
            else:
                self.coeff[code] = df[cols]
        # This is used in the case of the convolution method. We compute the
        # probability of occurrence for discrete intervals of ground motion
        # and we prepare values of median amplification and std for the
        # midlevels (i.e. ground motion on rock) for each IMT
        if amplevels is not None:
            self.imtls = imtls
            self.levels = levels
            self._set_alpha_sigma(mag=None, dst=None)

    def _set_alpha_sigma(self, mag, dst):
        """
        This sets the median amplification and std
        """
        imtls = self.imtls
        levels = self.levels
        self.midlevels = numpy.diff(levels) / 2 + levels[:-1]  # shape I-1
        self.ialphas = {}  # code -> array of length I-1
        self.isigmas = {}  # code -> array of length I-1
        for code in self.coeff:
            df = self.coeff[code]
            if mag is not None:
                # Reducing the initial dataframe by keeping information just
                # for the given magnitude and distance
                magu = numpy.sort(numpy.unique(df['from_mag']))
                magsel = magu[max(numpy.argwhere(magu < mag))[0]]
                df = df.loc[df['from_mag'] == magsel, :]
                dstu = numpy.sort(numpy.unique(df['from_rrup']))
                dstsel = dstu[max(numpy.argwhere(dstu < dst))[0]]
                df = df.loc[df['from_rrup'] == dstsel, :]
            for imt in imtls:
                self.ialphas[code, imt], self.isigmas[code, imt] = (
                    self._interp(code, imt, self.midlevels, df))

    def check(self, vs30, vs30_tolerance, gsims_by_trt):
        """
        Raise a ValueError if some vs30 is different from vs30_ref
        within the tolerance. Called by the engine.
        """
        for gsims in gsims_by_trt.values():
            for gsim in gsims:
                if vs30_tolerance < 0:
                    continue
                elif not hasattr(gsim, 'DEFINED_FOR_REFERENCE_VELOCITY'):
                    raise AttributeError(
                        f'The attribute DEFINED_FOR_REFERENCE_VELOCITY is'
                        f' missing in the gsim {gsim}. However, at your peril,'
                        f' you can disable the vs30 consistency check by'
                        f' setting vs30_tolerance = -1')
                gsim_ref = gsim.DEFINED_FOR_REFERENCE_VELOCITY
                if gsim_ref and gsim_ref < self.vs30_ref:
                    raise ValueError(
                        '%s.DEFINED_FOR_REFERENCE_VELOCITY=%s < %s'
                        % (gsim.__class__.__name__, gsim_ref, self.vs30_ref))
        if vs30_tolerance < 0:
            return
        if (numpy.abs(vs30 - self.vs30_ref) > vs30_tolerance).any():
            raise ValueError('Some vs30 in the site collection is different '
                             'from vs30_ref=%d over the tolerance of %d' %
                             (self.vs30_ref, vs30_tolerance))

    def amplify_one(self, ampl_code, imt, poes):
        """
        :param ampl_code: code for the amplification function
        :param imt: an intensity measure type
        :param poes: the original PoEs as an array of shape (I, G)
        :returns: the amplified PoEs as an array of shape (A, G)
        """
        if isinstance(poes, list):  # in the tests
            poes = numpy.array(poes).reshape(-1, 1)
        # Manage the case of a site collection with empty ampcode
        if ampl_code == b'' and len(self.ampcodes) == 1:
            ampl_code = self.ampcodes[0]

        min_gm = numpy.amin(self.imtls[imt])
        max_gm = numpy.amax(self.imtls[imt])

        min_ratio = numpy.amin(numpy.array(self.amplevels[1:]) /
                               numpy.array(self.amplevels[:-1]))*0.9
        min_ratio = min(max(min_ratio, 1.05), 1.1)
        allimls = [min_gm]
        while allimls[-1] < max_gm:
            allimls.append(allimls[-1]*min_ratio)
        allimls = numpy.array(allimls)

        A, G = len(self.amplevels), poes.shape[1]
        ampl_poes = numpy.zeros((A, G))

        # Amplify, for each site i.e. distance
        for g in range(G):

            # Compute the probability of occurrence of GM within a number of
            # intervals by interpolating the hazard curve
            idx = numpy.nonzero(poes[:, g].flatten() > 1e-100)
            simls = allimls[allimls <= numpy.amax(self.imtls[imt][idx])]
            ipoes = numpy.interp(numpy.log10(simls),
                                 numpy.log10(self.imtls[imt][idx]),
                                 numpy.log10(poes[:, g].flatten()[idx]))
            ipoes = 10.0**ipoes
            p_occ = -numpy.diff(ipoes)

            # Calculate the amplification factor and sigma for the selected
            # IMLs
            self.levels = simls
            self._set_alpha_sigma(mag=None, dst=None)
            ialphas = self.ialphas[ampl_code, imt]
            isigmas = self.isigmas[ampl_code, imt]

            for mid, p, a, s in zip(self.midlevels, p_occ, ialphas, isigmas):
                #
                # This computes the conditional probabilities of exceeding
                # defined values of shaking on soil given a value of shaking
                # on rock. 'mid' is the value of ground motion on rock to
                # which we associate the probability of occurrence 'p'. 'a'
                # is the median amplification factor and 's' is the standard
                # deviation of the logarithm of amplification.
                #
                # In the case of an amplification function without uncertainty
                # (i.e. sigma is zero) this will return values corresponding
                # to 'p' times 1 (if the value of shaking on rock will be
                # larger than the value of shaking on soil) or 0 (if the
                # value of shaking on rock will be smaller than the value of
                # shaking on soil)
                #
                logaf = numpy.log(self.amplevels/mid)
                ampl_poes[:, g] += (1.0-norm_cdf(logaf, numpy.log(a), s)) * p
        return ampl_poes

    def amplify(self, ampl_code, hcurve):
        """
        :param ampl_code: 2-letter code for the amplification function
        :param hcurve: an array of shape (L*M, R)
        :returns: amplified array of shape (A*M, R)
        """
        new = [self.amplify_one(ampl_code, imt, hcurve[self.imtls(imt)])
               for imt in self.imtls]
        return numpy.concatenate(new)

    def _interp(self, ampl_code, imt_str, imls, coeff=None):
        # returns ialpha, isigma for the given levels
        if coeff is None:
            coeff = self.coeff[ampl_code]

        if len(coeff) == 1:  # there is single coefficient for all levels
            ones = numpy.ones_like(imls)
            ialpha = coeff[imt_str].iloc[0] * ones
            try:
                isigma = coeff['sigma_' + imt_str].iloc[0] * ones
            except KeyError:
                isigma = numpy.zeros_like(imls)  # shape E
        else:
            alpha = coeff[imt_str]
            try:
                sigma = coeff['sigma_' + imt_str]
            except KeyError:
                isigma = numpy.zeros_like(imls)  # shape E
            else:
                isigma = numpy.interp(imls, alpha.index, sigma)  # shape E
            ialpha = numpy.interp(imls, alpha.index, alpha)  # shape E
        return ialpha, isigma

    def _amplify_gmvs(self, ampl_code, gmvs, imt_str, rng):
        # gmvs is an array of shape E
        ialpha, isigma = self._interp(ampl_code, imt_str, gmvs)
        uncert = rng.normal(numpy.zeros_like(gmvs), isigma)
        return numpy.exp(numpy.log(ialpha * gmvs) + uncert)

    def amplify_gmfs(self, ampcodes, gmvs, imts, seed=0):
        """
        Amplify in-place the gmvs array of shape (M, N, E)

        :param ampcodes: N codes for the amplification functions
        :param gmvs: ground motion values
        :param imts: intensity measure types
        :param seed: seed used when adding the uncertainty
        """
        rng = numpy.random.default_rng(seed)
        for m, imt in enumerate(imts):
            for i, (ampcode, arr) in enumerate(zip(ampcodes, gmvs[m])):
                gmvs[m, i] = self._amplify_gmvs(ampcode, arr, str(imt), rng)


def get_poes_site(mean_std, cmaker, ctx):
    """
    NOTE: this works for a single site

    :param mean_std:
        See :function:`openquake.hazardlib.gsim.base.get_poes`
    :param cmaker:
        A :class:`openquake.hazardlib.contexts.ContextMaker` instance
    :param truncation_level:
        The level of truncation of the normal distribution of ground-motion
        on rock
    :param ampl:
        Site amplification function instance of
        :class:openquake.hazardlib.site_amplification.AmpFunction
    :param ctx:
        Context object with attributes .mag, .sites, .rrup
    """
    # Mean and std of ground motion for the IMTs considered in this analysis
    # C - Number of contexts
    # L - Number of intensity measure levels
    loglevels = cmaker.loglevels
    phi_b = cmaker.phi_b
    af = cmaker.oq.af
    mean, stddev = mean_std  # shape (C, M)
    C, L = mean.shape[1], loglevels.size
    assert len(numpy.unique(ctx.sids)) == 1  # 1 site
    M = len(loglevels)
    L1 = L // M

    # This is the array where we store the output results i.e. poes on soil
    out_s = numpy.zeros((C, L))

    # `nsamp` is the number of IMLs per IMT used to compute the hazard on rock
    # while 'L' is total number of ground-motion values
    nsamp = 40

    # Compute the probability of exceedance for each in intensity
    # measure type IMT
    sigma = af.get_max_sigma()
    mags = ctx.mag
    rrups = ctx.rrup
    [ampcode] = numpy.unique(ctx.ampcode)
    for m, imt in enumerate(loglevels):

        # Get the values of ground-motion used to compute the probability
        # of exceedance on soil.
        soillevels = loglevels[imt]  # shape L1

        # Here we set automatically the IMLs that will be used to compute
        # the probability of occurrence of GM on rock within discrete
        # intervals
        ll = numpy.linspace(min(soillevels) - sigma * 4.,
                            max(soillevels) + sigma * 4.,
                            num=nsamp)

        # Calculate for each ground motion interval the probability
        # of occurrence on rock for all the sites
        for iml_l, iml_u in zip(ll[:-1], ll[1:]):

            # Set the arguments of the truncated normal distribution
            # function
            out_l = (iml_l - mean[m]) / stddev[m]
            out_u = (iml_u - mean[m]) / stddev[m]

            # Probability of occurrence on rock
            pocc_rock = (truncnorm_sf(phi_b, out_l) -
                         truncnorm_sf(phi_b, out_u))  # shape C

            # Skipping cases where the pocc on rock is negligible
            if numpy.all(pocc_rock < 1e-10):
                continue

            # Ground-motion value in the middle of each interval
            iml_mid = (numpy.exp(iml_l) + numpy.exp(iml_u)) / 2.

            # Get mean and std of the amplification function for this
            # magnitude, distance and IML
            median_af, std_af = af.get_mean_std(  # shape C
                ampcode, imt, iml_mid, mags, rrups)

            # Computing the probability of exceedance of the levels of
            # ground-motion loglevels on soil
            logaf = numpy.log(numpy.exp(soillevels) / iml_mid)  # shape L1
            for li in range(L1):
                poex_af = 1. - norm.cdf(
                    logaf[li], numpy.log(median_af), std_af)  # shape C
                out_s[:, m * L1 + li] += poex_af * pocc_rock  # shape C

    return out_s
