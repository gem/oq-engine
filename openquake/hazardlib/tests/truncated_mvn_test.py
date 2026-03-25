# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026, GEM Foundation
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

import numpy as np
from openquake.hazardlib.truncated_mvn import TruncatedMVN, FastTruncatedMVN


def test():
    d = 10  # dimensions

    # random mu and cov
    mu = np.random.rand(d)
    cov = 0.5 - np.random.rand(d ** 2).reshape((d, d))
    cov = np.triu(cov)
    cov += cov.T - np.diag(cov.diagonal())
    cov = np.dot(cov, cov)

    # constraints
    lb = np.zeros_like(mu) - 1
    ub = np.ones_like(mu) * np.inf

    # create truncated normal and sample from it
    n_samples = 10000
    tmvn = TruncatedMVN(mu, cov, lb, ub, seed=42)
    samples = tmvn.sample(n_samples)  # shape (d, n)

    fmvn = FastTruncatedMVN(mu, cov, lb, ub, seed=42)
    samps = fmvn.sample(n_samples)
    breakpoint()

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2)
    ax[0].hist(samples[0], 15, (-4, 4))
    ax[1].hist(samps[0], 15, (-4, 4))
    plt.show()
