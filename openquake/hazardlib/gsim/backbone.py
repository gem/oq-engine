# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
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
Shared computation for GSIM branches with additive mean shifts.

Logic trees often contain several branches of the same GSIM differing
only in an option shifting the result, like ``sigma_mu_epsilon=-1.36, 0,
+1.36`` for ``BooreEtAl2014``. Running the full ``compute`` for each
branch is wasteful: GSIMs can declare instead how to split the
computation in a central part, common to all the branches and computed
once, and a cheap shift, applied to each branch.

Opting in
---------

A GSIM opts in with two class attributes::

    class BooreEtAl2014(GMPE):
        central_functions = (compute_without_shift, _apply_nshm_shift)
        shifted_options = ('sigma_mu_epsilon',)

``central_functions`` is a pair of functions:

``compute_central(gsim, ctx, imts, mean, sig, tau, phi, gra_mon)``
    fills the four output arrays with the part common to all the
    branches and returns a ``resolved`` object with whatever the shifts
    need later, usually ``ctx``; it can also be a tuple like
    ``(ctx, adjustments)`` in ``KuehnEtAl2020SInter`` or the grid
    adjustments in ``GridAdjustedGMPE``.

``apply_branch(gsim, resolved, imts, mean, sig, tau, phi)``
    modifies the arrays in place, using only the shifted options of the
    branch and ``resolved``; it can use ``resolved`` as a cache shared by
    the branches (as ``KuehnEtAl2020SInter`` does), but it must not
    modify it otherwise.

The two functions must satisfy one rule: ``compute_central`` followed by
``apply_branch`` must give the same result as ``gsim.compute``. The
simplest way to guarantee it is to give ``compute`` an ``apply_shift``
flag, calling the shift at the end, and to use :func:`compute_without_shift`
as ``compute_central``::

    def apply_sigma_mu(gsim, ctx, imts, mean, *_stddevs):
        if gsim.sigma_mu_epsilon:
            for m, imt in enumerate(imts):
                mean[m] += gsim.sigma_mu_epsilon * gsim.COEFFS[imt]['sm']

    class MyGMPE(GMPE):
        central_functions = (compute_without_shift, apply_sigma_mu)
        shifted_options = ('sigma_mu_epsilon',)

        def __init__(self, sigma_mu_epsilon=0.):
            self.sigma_mu_epsilon = sigma_mu_epsilon

        def compute(self, ctx: numpy.recarray, imts, mean, sig, tau, phi,
                    apply_shift=True):
            ...  # the expensive part
            if apply_shift:
                apply_sigma_mu(self, ctx, imts, mean)

The central key
---------------

At instantiation time the GSIM metaclass sets ``gsim.central_key`` with
:func:`openquake.hazardlib.gsim.base.get_central_key`: the class name and
the repr of all the options except the ``shifted_options`` (and the
weight). The key is None, i.e. the GSIM is computed independently, if
a subclass overrides ``compute`` without redeclaring ``shifted_options``
(the central functions would bypass its ``compute``) or if an option is
not a Python literal (for instance the repr of a large numpy array is
truncated). A ``ModifiableGMPE`` with modifiers which are not independent
scalings disables the sharing by setting ``central_functions = ()`` on
the instance. Since the key is computed only once, a GSIM must not be
modified after its instantiation.

The computation
---------------

``ContextMaker.get_mean_stds`` computes normally the GSIMs without
central functions or without a key, and groups the others by
``(central_functions, central_key)``. For each group and context slice
it calls ``compute_central`` once, on the first GSIM of the group and
writing directly in its output slot; then it loops on the branches in
reverse order: each branch copies the central result in its own slot
and calls ``apply_branch`` on it. The first branch is shifted last since
its slot holds the central result until all the other branches have
copied it::

    branches:  eps=-1.36   eps=0    eps=+1.36      (same key)
                    \\        |        /
               compute_central  (once, into slot 0)
                    /        |        \\
          copy + shift   copy + shift   shift slot 0 last

Since the cost of ``compute`` is in the central part (backbone,
interpolations, raytracing) and a shift is usually a few array additions,
a group of N branches costs about one ``compute`` instead of N.
"""


def compute_without_shift(gsim, ctx, imts, mean, sig, tau, phi, gra_mon=None):
    """Compute the shared predictions and pass the context to the shift."""
    gsim.compute(ctx, imts, mean, sig, tau, phi, apply_shift=False)
    return ctx
