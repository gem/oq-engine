"""
Figure 6 check for the Moss and Ross (2011) primary fault displacement model.

Moss and Ross (2011) Figure 6 is a plotted curve rather than a tabulated
benchmark. These digitized values are therefore used as a paper-consistency
check with loose tolerances, not as an exact reference table.
"""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from openquake.pfd.primary_surf_displ import MossRoss2011PrimaryFD

pytestmark = pytest.mark.unit


FIG6_DIGITIZED = {
    5.5: {
        "displacement_m": np.array([
            0.01, 0.02, 0.03, 0.05, 0.07, 0.10, 0.15, 0.20, 0.25,
            0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 1.00, 1.20, 1.50,
            1.70,
        ]),
        "prob_exceed": np.array([
            0.998, 0.980, 0.978, 0.974, 0.936, 0.881, 0.784, 0.685,
            0.586, 0.501, 0.367, 0.258, 0.183, 0.129, 0.090, 0.052,
            0.030, 0.012, 0.008,
        ]),
    },
    6.5: {
        "displacement_m": np.array([
            0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50, 0.70,
            1.00, 1.50, 2.00, 3.00, 5.00, 10.00,
        ]),
        "prob_exceed": np.array([
            1.00, 1.00, 0.99, 0.97, 0.88, 0.79, 0.60, 0.44,
            0.26, 0.11, 0.06, 0.02, 0.00, 0.00,
        ]),
    },
    7.5: {
        "displacement_m": np.array([
            0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50, 0.70,
            1.00, 1.50, 2.00, 3.00, 5.00, 10.00,
        ]),
        "prob_exceed": np.array([
            1.00, 1.00, 1.00, 1.00, 0.97, 0.94, 0.86, 0.78,
            0.65, 0.42, 0.28, 0.15, 0.04, 0.00,
        ]),
    },
}


@pytest.mark.parametrize("mag", [5.5, 6.5, 7.5])
def test_moss_ross2011_fig6_ad_x_l_025_matches_digitized_paper_curve(mag):
    """
    Compare P(D > d | m, slip) against digitized Figure 6 values.

    Scenario: reverse faulting, x/L = 0.25, AD-normalized displacement, gamma
    spatial variability model. The tolerance reflects digitization uncertainty
    and plotting/rounding in the paper figure.
    """
    model = MossRoss2011PrimaryFD()
    digitized = FIG6_DIGITIZED[mag]

    actual = model.get_prob(
        d=digitized["displacement_m"],
        X_L_ratio=[0.25],
        mag=mag,
        norm_disp_type="AD",
    )[:, 0]

    assert_allclose(actual, digitized["prob_exceed"], rtol=0.0, atol=0.05)
