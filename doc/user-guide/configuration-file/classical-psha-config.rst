.. _classical-psha-params:

Classical PSHA
--------------

In the following, we describe the overall structure and the most typical parameters of a configuration file to be used 
for the computation of a seismic hazard map using a classical PSHA methodology.

**********
logic-tree
**********

The OpenQuake engine provides two options for processing the whole logic tree structure.

The first option uses Montecarlo sampling; the user in this case specifies a number of realizations 
and a ``random_seed`` parameter, used to control the random generator so that when Monte Carlo
procedures are used calculations are replicable (if the same ``random_seed`` is used you get exactly 
the same results).

In the second option, all the possible realizations are created. Below we provide an example of the latter option. 
In this case, we set the ``number_of_logic_tree_samples`` to 0. OpenQuake engine will perform a
complete enumeration of all the possible paths from the roots to the leaves of the logic tree structure::

	[logic_tree]
	number_of_logic_tree_samples = 0

If the seismic source logic tree and the ground motion logic tree do not contain epistemic uncertainties the engine will 
create a single PSHA input.

*Generation of the earthquake rupture forecast*::

	[erf]
	rupture_mesh_spacing = 5
	width_of_mfd_bin = 0.1
	area_source_discretization = 10

This section of the configuration file is used to specify the level of discretization of the mesh representing faults, 
the grid used to delineate the area sources and, the magnitude-frequency distribution. Note that the smaller is the mesh 
spacing (or the bin width) the larger are (1) the precision in the calculation and (2) the computation demand.

In cases where the source model may contain a mixture of simple and complex ruptures, it is possible to define a 
different rupture mesh spacing for complex faults only. This may be helpful in models that permit floating ruptures over 
large subduction sources, in which the nearest source-to-site distances may be larger than 20 - 30 km, and for which a 
small mesh spacing would produce a very large number of ruptures. The spacing for complex faults only can be configured 
by the line::

	complex_fault_mesh_spacing = 10

***********
calculation
***********

This section of the OpenQuake engine configuration file specifies the parameters that are relevant to the calculation 
of hazard. These include the names of the two files containing the Seismic Source System and the Ground Motion System, 
the duration of the time window used to compute the hazard, the ground motion intensity measure types and levels for 
which the probability of exceedance will be computed, the level of truncation of the Gaussian distribution of the 
the logarithm of ground motion used in the calculation of hazard and the maximum integration distance (i.e. the distance 
within which sources will contribute to the computation of the hazard)::

	[calculation]
	source_model_logic_tree_file = source_model_logic_tree.xml
	gsim_logic_tree_file = gmpe_logic_tree.xml
	investigation_time = 50.0
	intensity_measure_types_and_levels = {"PGA": [0.005, ..., 2.13]}
	truncation_level = 3
	maximum_distance = 200.0

The maximum distance refers to the largest distance between a rupture and the target calculation sites for the 
rupture to be considered in the PSHA calculation. This can be input directly in terms of kilometres (as above). There 
may be cases, however, in which it may be appropriate to have a different maximum source-to-site distance depending on 
the tectonic region type. This may be used, for example, to eliminate the impact of small, very far-field sources in 
regions of high attenuation (in which case the maximum distance is reduced), or conversely, it may be raised to allow certain 
source types to contribute to the hazard at greater distances (such as in the case when the region has lower attenuation). 
An example configuration for a maximum distance in Active Shallow Crust of 150 km, and in Stable Continental Crust of 
200 km, is shown below::

	maximum_distance = {'Active Shallow Crust': 150.0,
	                    'Stable Continental Crust': 200.0}

******
output
******

The final section of the configuration file contains the parameters controlling the types of output to 
be produced. Providing an export directory will tell the OpenQuake engine where to place the output files when the ``--exports`` flag 
is used when running the program. Setting ``mean`` to true will result in a specific output containing the mean curves of 
the logic tree, likewise quantiles will produce separate files containing the ``quantile`` hazard curves at the quantiles 
listed (0.1, 0.5 and 0.9 in the example above, leave blank or omit if no quantiles are required). Setting 
``uniform_hazard_spectra`` to true will output the uniform hazard spectra at the same probabilities of exceedance (poes) as 
those specified by the later option ``poes``. The probabilities specified here correspond to the set investigation time. 
Specifying poes will output hazard maps. For more information about the outputs of the calculation, see the section: 
“Description of hazard output” (page)::

	[output]
	export_dir = outputs/
	# given the specified `intensity_measure_types_and_levels`
	mean = true
	quantiles = 0.1 0.5 0.9
	uniform_hazard_spectra = false
	poes = 0.1

Seismic Hazard Disaggregation
-----------------------------

In this section, we describe the structure of the configuration file to be used to complete a seismic hazard 
disaggregation. Since only a few parts of the standard configuration file need to be changed we can use the description 
given in the section above, :ref:`Classical PSHA <classical-psha-params>`, as a reference and we emphasize herein major differences::

	[general]
	description = A demo job.ini file for PSHA disaggregation
	calculation_mode = disaggregation
	random_seed = 1024

The calculation mode parameter in this case is set as ``disaggregation``.

********
geometry
********

In the section, it is necessary to specify the geographic coordinates of the site(s) where the disaggregation will be 
performed. The coordinates of multiple sites should be separated with a comma::

	[geometry]
	sites = 11.0 44.5, 11.1 44.7, 11.2 44.9

**************
disaggregation
**************

The disaggregation parameters need to be added to the standard configuration file. They are shown in the following 
example and a description of each parameter is provided below::

	[disaggregation]
	poes_disagg = 0.02, 0.1
	mag_bin_width = 1.0
	distance_bin_width = 25.0
	coordinate_bin_width = 1.5
	num_epsilon_bins = 3
	disagg_outputs = Mag_Dist_Eps Mag_Lon_Lat
	num_rlzs_disagg = 3

- ``poes_disagg``: disaggregation is performed for the intensity measure levels corresponding to the probability of exceedance value(s) provided here. The computations use the ``investigation_time`` and the ``intensity_measure_types_and_levels`` defined in the “Calculation configuration” section. For the ``poes_disagg`` the intensity measure level(s) for the disaggregation are inferred by performing a classical calculation and by inverting the mean hazard curve. NB: this has changed in engine 3.17. In previous versions, the inversion was made on the individual curves which meant some realizations could be discarded if the PoEs could not be reached.
- ``iml_disagg``: the intensity measure level(s) to be disaggregated can be directly defined by specifying ``iml_disagg``. Note that a disaggregation computation requires either ``poes_disagg`` or ``iml_disagg`` to be defined, but both cannot be defined at the same time.
- ``mag_bin_width``: mandatory; specifies the width of every magnitude histogram bin of the disaggregation matrix computed
- ``distance_bin_width``: specifies the width of every distance histogram bin of the disaggregation matrix computed (km)
- ``coordinate_bin_width``: specifies the width of every longitude-latitude histogram bin of the disaggregation matrix computed (decimal degrees)
- ``num_epsilon_bins``: mandatory; specifies the number of Epsilon histogram bins of the disaggregation matrix. The width of the Epsilon bins depends on the ``truncation_level`` defined in the “Calculation configuration” section (page)
- ``disagg_outputs``: optional; specifies the type(s) of disaggregation to be computed. The options are: ``Mag``, ``Dist``, ``Lon_Lat``, ``Lon_Lat_TRT``, ``Mag_Dist``, ``Mag_Dist_Eps``, ``Mag_Lon_Lat``, ``TRT``. If none are specified, then all are computed. More details of the disaggregation output are given in the “Outputs from Hazard Disaggregation” section)
- ``disagg_by_src``: optional; if specified and set to true, disaggregation by source is computed, if possible.
- ``num_rlzs_disagg``: optional; specifies the number of realizations to be used, selecting those that yield intensity measure levels closest to the mean. Starting from engine 3.17 the default is 0, which means considering all realizations.

Alternatively to ``num_rlzs_disagg``, the user can specify the index or indices of the realizations to disaggregate as a 
list of comma-separated integers. For example::

	[disaggregation]
	rlz_index = 22,23

If ``num_rlzs_disagg`` is specified, the user cannot specify ``rlz_index``, and vice versa. If ``num_rlzs_disagg`` or 
``rlz_index`` is specified, then the mean disaggregation is automatically computed from the selected realizations.

As mentioned above, the user also has the option to perform disaggregation by directly specifying the intensity measure 
level to be disaggregated, rather than specifying the probability of exceedance. An example is shown below::

	[disaggregation]
	iml_disagg = {'PGA': 0.1}

If ``iml_disagg`` is specified, the user should not include ``intensity_measure_types_and_levels`` in the 
“Calculation configuration” section since it is explicitly given here.

The OpenQuake engine supports the calculation of two typologies of disaggregation results involving the parameter epsilon. 
The standard approach used by the OpenQuake engine is described in the :ref:`Underlying Science <underlying-science>` tab. The reader 
interested in learning more about the parameter :math:`\epsilon^{*}` can refer to the PEER report `Probabilistic Seismic Hazard 
Analysis Code Verification, PEER Report 2018-03 <https://peer.berkeley.edu/publications/2018-03>`_.

To obtain disaggregation results in terms of :math:`\epsilon^{*}` the additional line below must be added to the disaggregation 
section of the configuration file::

	[disaggregation]
	epsilon_star = True

