# --------------- POINT - Propagation Of epIstemic uNcerTainty ----------------
# Copyright (C) 2025 GEM Foundation
#
#                `.......      `....     `..`...     `..`... `......
#                `..    `..  `..    `..  `..`. `..   `..     `..
#                `..    `..`..        `..`..`.. `..  `..     `..
#                `.......  `..        `..`..`..  `.. `..     `..
#                `..       `..        `..`..`..   `. `..     `..
#                `..         `..     `.. `..`..    `. ..     `..
#                `..           `....     `..`..      `..     `..
#
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# coding: utf-8

import pathlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from openquake.hazardlib.nrml import to_python
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.geo.surface import SimpleFaultSurface
from openquake.hazardlib.geo.mesh import Mesh

# This file folder
TFF = pathlib.Path(__file__).parent.resolve()


def main():
    """
    Plot sources and sites
    """

    # Source converter
    sconv = SourceConverter(
        investigation_time=1.,
        rupture_mesh_spacing=5.,
        width_of_mfd_bin=0.1)

    # Reading sites
    fname = TFF / "sites.csv"
    df = pd.read_csv(fname)

    # Reading the first source and create the surface
    fname = TFF / "ssm_a.xml"
    ssm = to_python(fname, sconv)
    srca = ssm[0][0]
    sfca = SimpleFaultSurface.from_fault_data(
        fault_trace=srca.fault_trace,
        upper_seismogenic_depth=srca.upper_seismogenic_depth,
        lower_seismogenic_depth=srca.lower_seismogenic_depth,
        dip=srca.dip,
        mesh_spacing=2.5
    )

    # Reading the second source and create the surface
    fname = TFF / "ssm_b.xml"
    ssm = to_python(fname, sconv)
    srcb = ssm[0][0]
    sfcb = SimpleFaultSurface.from_fault_data(
        fault_trace=srcb.fault_trace,
        upper_seismogenic_depth=srcb.upper_seismogenic_depth,
        lower_seismogenic_depth=srcb.lower_seismogenic_depth,
        dip=srcb.dip,
        mesh_spacing=2.5
    )

    # Create the mesh
    bbs = {}
    bbs['a'] = sfca.get_bounding_box()
    bbs['b'] = sfcb.get_bounding_box()
    bb = np.zeros(4)
    for key in bbs:
        bb[[0, 3]] = [np.min([bb[i], bbs[key][i]]) for i in [0, 3]]
        bb[[1, 2]] = [np.max([bb[i], bbs[key][i]]) for i in [1, 2]]
    dlt = 0.5
    bb[0] -= dlt
    bb[1] += dlt
    bb[2] += dlt
    bb[3] -= dlt

    lons = []
    lats = []
    step = 0.025

    ulo = np.arange(bb[0], bb[1], step)
    ula = np.arange(bb[3], bb[2], step)

    lons = np.zeros((len(ula), len(ulo)))
    lats = np.zeros((len(ula), len(ulo)))
    for i_lo, lo in enumerate(ulo):
        for i_la, la in enumerate(ula):
            lons[i_la, i_lo] = lo
            lats[i_la, i_lo] = la
    mesh = Mesh(lons.flatten(), lats.flatten())

    # Compute rjb
    rjb_a = sfca.get_joyner_boore_distance(mesh).reshape(lons.shape)
    rjb_b = sfcb.get_joyner_boore_distance(mesh).reshape(lons.shape)
    dmax = np.amax([np.amax(rjb_a), np.amax(rjb_b)])

    # Plotting
    fig, axs = plt.subplots(1, 1)
    plt.plot(
        srca.fault_trace.coo[:, 0],
        srca.fault_trace.coo[:, 1],
        '-g',
        lw=2.0
    )
    plt.plot(
        srcb.fault_trace.coo[:, 0],
        srcb.fault_trace.coo[:, 1],
        '-g',
        lw=2.0
    )

    cs = axs.contour(lons, lats, rjb_a, colors='blue')
    labs = {}
    for val in cs.levels:
        labs[val] = f"{val:.0f}"
    axs.clabel(cs, cs.levels[::2], fmt=labs, fontsize=10)

    cs = axs.contour(lons, lats, rjb_b, colors='red', linestyles='--')
    labs = {}
    for val in cs.levels:
        labs[val] = f"{val:.0f}"
    axs.clabel(cs, cs.levels[::2], fmt=labs, fontsize=10)

    plt.plot(sfca.mesh.lons, sfca.mesh.lats, '.b', label="src A", alpha=0.5)
    plt.plot(sfcb.mesh.lons, sfcb.mesh.lats, '.r', label="src B", alpha=0.5)

    plt.plot(df.lon, df.lat, 's', color='purple', ms=0.75)
    for i_row, row in df.iterrows():
        plt.text(row.lon, row.lat, s=row.custom_site_id)

    plt.show()


if __name__ == "__main__":
    main()
