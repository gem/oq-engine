The Classical Probabilistic Seismic Hazard Analysis (cPSHA) approach facilitates calculation of hazard curves and hazard maps following the classical integration procedure (Cornell [1968], McGuire [1976]) as formulated by Field et al. [2003].

Sources:

* Cornell, C. A. (1968).
  Engineering seismic risk analysis.
  Bulletin of the Seismological Society of America, 58:1583–1606.

* Field, E. H., Jordan, T. H., and Cornell, C. A. (2003).
  OpenSHA - A developing Community-Modeling
  Environment for Seismic Hazard Analysis. Seism. Res. Lett., 74:406–419.

* McGuire, K. K. (1976).
  Fortran computer program for seismic risk analysis. Open-File report 76-67,
  United States Department of the Interior, Geological Survey. 102 pages.

### Inputs

The inputs for a Classical hazard calculation consist of a handful of plain-text and XML files. They are as follows:

* INI-style config file
* source model(s)
* source model logic tree
* GSIM logic tree
* site model (optional)
  - If no site model is specified, the config file must define reference parameters to be used for all locations

#### Config file

Here's an example Classical config file:

<pre>
[general]

description = Simple Fault Demo, Classical PSHA
calculation_mode = classical
random_seed = 23

[geometry]

region = 6.5 45.8, 6.5 46.5, 8.5 46.5, 8.5 45.8
# km
region_grid_spacing = 10.0

[logic_tree]

number_of_logic_tree_samples = 2

[erf]

# km
rupture_mesh_spacing = 5
width_of_mfd_bin = 0.2
# km
area_source_discretization = 10

[site_params]

reference_vs30_type = measured
reference_vs30_value = 760.0
reference_depth_to_2pt5km_per_sec = 5.0
reference_depth_to_1pt0km_per_sec = 100.0

[calculation]

source_model_logic_tree_file = source_model_logic_tree.xml
gsim_logic_tree_file = gmpe_logic_tree.xml
# years
investigation_time = 50.0
intensity_measure_types_and_levels = {"PGA": [0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527, 0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778, 1.09, 1.52, 2.13], "SA(0.025)": [0.005, 0.007, 0.0098, 0.0137, 0.0192, 0.0269, 0.0376, 0.0527, 0.0738, 0.103, 0.145, 0.203, 0.284, 0.397, 0.556, 0.778, 1.09, 1.52, 2.13]}
truncation_level = 3
# km
maximum_distance = 200.0

[output]

export_dir = /tmp/xxx
mean_hazard_curves = true
quantile_hazard_curves = 0.15, 0.85
poes_hazard_maps = 0.1 0.2
</pre>

TODO: Document each parameter in detail.

#### Source model(s)

NRML XML files containing definition of the seismic sources to consider for this calculation. Seismic source definitions include source type (simple fault, complex fault, point, or area), geometry, and Magnitude-Frequency Distribution (MFD).

#### Source Model Logic Tree

TODO:

#### GSIM (Ground Shaking Intensity Model) Logic Tree

TODO:

#### Site Model (optional)

TODO:

### Post-Processing

The Classical calculator by default computes hazard curves for each location of interest for all logic tree realizations. As an option, users can also compute mean and quantile hazard curves, aggregated over all logic tree realizations.

To compute mean curves, set the following config file parameter:

<pre>mean_hazard_curves = true</pre>

To turn this feature off, simply set the parameter to `false`.

To compute quantile curves, set the following config file parameter to specify one or more quantile levels (in the range [0.0, 1.0]):

<pre>quantile_hazard_curves = 0.15, 0.85</pre>

To turn this feature off, simply leave the parameter blank:

<pre>quantile_hazard_curves =</pre>

Outputs

TODO