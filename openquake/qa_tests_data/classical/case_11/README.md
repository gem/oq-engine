## Overview

Classical PSHA calculation for five sites using `GridAdjustedGMPE` with
`AkkarEtAlRjb2014` as the underlying GMM to be adjusted. Three h3-gridded
residual correction terms are applied (`dL2L`, `dS2S`, `adj_per_km`) for
PGA and SA(0.5) to both the mean predicted ground-motion and the mapped
sigma component (can be total, tau or phi). SA(1.0) has no grid data and
therefore receives no adjustment intentionally. The visualisation of the
hdf5 clearly shows that the h3 grids can vary in density - this is
intentional, with the `GridAdjustedGMPE` supporting either constant or
varying density h3 grid cells.

The hdf5 containing the corrections used in this simple test case is called
`grid_adjustments.hdf5`.

## A Visualisation of the Grid in the HDF5

![Grid adjustments overview](grid_adjustments_overview.png)

The figure shows the 3 mean adjustments for PGA. Per-cell `{term}_sig`
reduction datasets also exist for each of the 3 terms in the hdf5 (not
shown in the figure):

| Panel  | Content                                                                                                  |
| ------ | -------------------------------------------------------------------------------------------------------- |
| left   | `dL2L`-based mean ground-motion correction per h3 cell (hypocentre lookup)                             |
| centre | `dS2S`-based mean ground-motion correction per h3 cell (site lookup)                                   |
| right  | `adj_per_km` which is path-based mean ground-motion correction (natural log units per km) (raytracing) |

Red star = hypocentre; green triangles = sites in the site model.

## Additional Information

It's advisable to consult the `GridAdjustedGMPE` GSIM module to fully understand this feature
if you plan to use it (`oq-engine/openquake/hazardlib/gsim/mgmpe/grid_adjusted_gmpe.py`).

Also, please note that the correction values provided in this test are arbitrary.
