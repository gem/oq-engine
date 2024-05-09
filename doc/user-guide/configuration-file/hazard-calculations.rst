Hazard Calculations
-------------------

.. _classical-psha:

**************
Classical PSHA
**************

In the following we describe the overall structure and the most typical parameters of a configuration file to be used 
for the computation of a seismic hazard map using a classical PSHA methodology.

**Calculation type and model info**::

	[general]
	description = A demo OpenQuake-engine .ini file for classical PSHA
	calculation_mode = classical
	random_seed = 1024

In this section the user specifies the following parameters:

- ``description``: a parameter that can be used to designate the model
- ``calculation_mode``: it is used to set the kind of calculation. In this case it corresponds to ``classical``. Alternative options for the calculation_mode are described later in this manual.
- ``random_seed``: is used to control the random generator so that when Monte Carlo procedures are used calculations are replicable (if the same ``random_seed`` is used you get exactly the same results).

**Geometry of the area (or the sites) where hazard is computed**

This section is used to specify where the hazard will be computed. Two options are available:

The first option is to define a polygon (usually a rectangle) and a distance (in km) to be used to discretize the 
polygon area. The polygon is defined by a list of longitude-latitude tuples.

An example is provided below::

	[geometry]
	region = 10.0 43.0, 12.0 43.0, 12.0 46.0, 10.0 46.0
	region_grid_spacing = 10.0

The second option allows the definition of a number of sites where the hazard will be computed. Each site is specified 
in terms of a longitude, latitude tuple. Optionally, if the user wants to consider the elevation of the sites, a value 
of depth [km] can also be specified, where positive values indicate below sea level, and negative values indicate above 
sea level (i.e. the topographic surface). If no value of depth is given for a site, it is assumed to be zero. An example 
is provided below::

	[geometry]
	sites = 10.0 43.0, 12.0 43.0, 12.0 46.0, 10.0 46.0

If the list of sites is too long the user can specify the name of a csv file as shown below::

	[geometry]
	sites_csv = <name_of_the_csv_file>

The format of the csv file containing the list of sites is a sequence of points (one per row) specified in terms of the 
longitude, latitude tuple. Depth values are again optional. An example is provided below::

	179.0,90.0
	178.0,89.0
	177.0,88.0

**Logic tree sampling**

The OpenQuake engine provides two options for processing the whole logic tree structure. The first option uses 
Montecarlo sampling; the user in this case specifies a number of realizations.

In the second option all the possible realizations are created. Below we provide an example for the latter option. In 
this case we set the ``number_of_logic_tree_samples`` to 0. OpenQuake engine will perform a complete enumeration of all the 
possible paths from the roots to the leaves of the logic tree structure.::

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

In cases where the source model may contain a mixture of simple and complex ruptures it is possible to define a 
different rupture mesh spacing for complex faults only. This may be helpful in models that permit floating ruptures over 
large subduction sources, in which the nearest source to site distances may be larger than 20 - 30 km, and for which a 
small mesh spacing would produce a very large number of ruptures. The spacing for complex faults only can be configured 
by the line::

	complex_fault_mesh_spacing = 10

**Parameters describing site conditions**::

	[site_params]
	reference_vs30_type = measured
	reference_vs30_value = 760.0
	reference_depth_to_2pt5km_per_sec = 5.0
	reference_depth_to_1pt0km_per_sec = 100.0

In this section the user specifies local soil conditions. The simplest solution is to define uniform site conditions 
(i.e. all the sites have the same characteristics).

Alternatively it is possible to define spatially variable soil properties in a separate file; the engine will then 
assign to each investigation location the values of the closest point used to specify site conditions.::

	[site_params]
	site_model_file = site_model.csv

The file containing the site model has the following structure::

	lon,lat,vs30,z1pt0,z2pt5,vs30measured,backarc
	10.0,40.0,800.0,19.367196734,0.588625072259,0,0
	10.1,40.0,800.0,19.367196734,0.588625072259,0,0
	10.2,40.0,800.0,19.367196734,0.588625072259,0,0
	10.3,40.0,800.0,19.367196734,0.588625072259,0,0
	10.4,40.0,800.0,19.367196734,0.588625072259,0,0

Notice that the 0 for the field ``vs30measured`` means that the ``vs30`` field is inferred, not measured. Most of the 
GMPEs are not sensitive to it, so you can usually skip it. For the ``backarc`` parameter 0 means false and this is the 
default, so you can skip such column. All columns that have defaults or are not needed by the GMPEs you are using can 
be skipped, while you will get an error if a relevant column is missing.

If the closest available site with soil conditions is at a distance greater than 5 km from the investigation location, a 
warning is generated.

**Note**: For backward-compatibility reasons, the site model file can also be given in XML format. That old format is 
deprecated but there are no plans to remove it any soon.

**Calculation configuration**::

	[calculation]
	source_model_logic_tree_file = source_model_logic_tree.xml
	gsim_logic_tree_file = gmpe_logic_tree.xml
	investigation_time = 50.0
	intensity_measure_types_and_levels = {"PGA": [0.005, ..., 2.13]}
	truncation_level = 3
	maximum_distance = 200.0

This section of the OpenQuake engine configuration file specifies the parameters that are relevant for the calculation 
of hazard. These include the names of the two files containing the Seismic Source System and the Ground Motion System, 
the duration of the time window used to compute the hazard, the ground motion intensity measure types and levels for 
which the probability of exceedence will be computed, the level of truncation of the Gaussian distribution of the 
logarithm of ground motion used in the calculation of hazard and the maximum integration distance (i.e. the distance 
within which sources will contribute to the computation of the hazard).

The maximum distance refers to the largest distance between a rupture and the target calculation sites in order for the 
rupture to be considered in the PSHA calculation. This can be input directly in terms of kilometres (as above). There 
may be cases, however, in which it may be appropriate to have a different maximum source to site distance depending on 
the tectonic region type. This may be used, for example, to eliminate the impact of small, very far-field sources in 
regions of high attenuation (in which case maximum distance is reduced), or conversely it may be raised to allow certain 
source types to contribute to the hazard at greater distances (such as in the case when the region has lower attenuation). 
An example configuration for a maximum distance in Active Shallow Crust of 150 km, and in Stable Continental Crust of 
200 km, is shown below::

	maximum_distance = {'Active Shallow Crust': 150.0,
	                    'Stable Continental Crust': 200.0}

**Output**::

	[output]
	export_dir = outputs/
	# given the specified `intensity_measure_types_and_levels`
	mean = true
	quantiles = 0.1 0.5 0.9
	uniform_hazard_spectra = false
	poes = 0.1

The final section of the configuration file is the one that contains the parameters controlling the types of output to 
be produced. Providing an export directory will tell OpenQuake engine where to place the output files when the ``--exports`` flag 
is used when running the program. Setting ``mean`` to true will result in a specific output containing the mean curves of 
the logic tree, likewise quantiles will produce separate files containing the ``quantile`` hazard curves at the quantiles 
listed (0.1, 0.5 and 0.9 in the example above, leave blank or omit if no quantiles are required). Setting 
``uniform_hazard_spectra`` to true will output the uniform hazard spectra at the same probabilities of exceedence (poes) as 
those specified by the later option ``poes``. The probabilities specified here correspond to the set investigation time. 
Specifying poes will output hazard maps. For more information about the outputs of the calculation, see the section: 
“Description of hazard output” (page).

**************************************
Seismic Hazard Disaggregation Analysis
**************************************

In this section we describe the structure of the configuration file to be used to complete a seismic hazard 
disaggregation. Since only a few parts of the standard configuration file need to be changed we can use the description 
given in Section :ref:`Classical PSHA <classical-psha>` as a reference and we emphasize herein major differences.::

	[general]
	description = A demo .ini file for PSHA disaggregation
	calculation_mode = disaggregation
	random_seed = 1024

The calculation mode parameter in this case is set as ``disaggregation``.

**Geometry of the area (or the sites) where hazard is computed**::

	[geometry]
	sites = 11.0 44.5

In the section it is necessary to specify the geographic coordinates of the site(s) where the disaggregation will be 
performed. The coordinates of multiple site should be separated with a comma.

**Disaggregation parameters**

The disaggregation parameters need to be added to the the standard configuration file. They are shown in the following 
example and a description of each parameter is provided below.::

	[disaggregation]
	poes_disagg = 0.02, 0.1
	mag_bin_width = 1.0
	distance_bin_width = 25.0
	coordinate_bin_width = 1.5
	num_epsilon_bins = 3
	disagg_outputs = Mag_Dist_Eps Mag_Lon_Lat
	num_rlzs_disagg = 3

- ``poes_disagg``: disaggregation is performed for the intensity measure levels corresponding to the probability of exceedance value(s) provided here. The computations use the ``investigation_time`` and the ``intensity_measure_types_and_levels`` defined in the “Calculation configuration” section. For the ``poes_disagg`` the intensity measure level(s) for the disaggregation are inferred by performing a classical calculation and by inverting the mean hazard curve. NB: this has changed in engine 3.17. In previous versions the inversion was made on the individual curves which meant some realizations could be discarded if the PoEs could not be reached.
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
``rlz_index`` are specified, the mean disaggregation is automatically computed from the selected realizations.

As mentioned above, the user also has the option to perform disaggregation by directly specifying the intensity measure 
level to be disaggregated, rather than specifying the probability of exceedance. An example is shown below::

	[disaggregation]
	iml_disagg = {'PGA': 0.1}

If ``iml_disagg`` is specified, the user should not include ``intensity_measure_types_and_levels`` in the 
“Calculation configuration” section since it is explicitly given here.

The OpenQuake engine supports the calculation of two typologies of disaggregation result involving the parameter epsilon. 
The standard approach used by the OpenQuake engine is described in the :ref:`OpenQuake engine Underlying Hazard Science Book <underlying-hazard-science>`. The reader 
interested in learning more about the parameter :math:`\epsilon^{*}` can refer to the PEER report `Probabilistic Seismic Hazard 
Analysis Code Verification, PEER Report 2018-03 <https://peer.berkeley.edu/publications/2018-03>`_.

To obtain disaggregation results in terms of :math:`\epsilon^{*}` the additional line below must be added to the disaggregation 
section of the configuration file::

	[disaggregation]
	epsilon_star = True

.. _event-based-psha:

****************
Event based PSHA
****************

In the following we describe the sections of the configuration file that are required to complete event based PSHA 
calculations.

**Calculation type and model info**

This part is almost identical to the corresponding one described in Section :ref:`Classical PSHA <classical-psha>`.

Note the setting of the ``calculation_mode`` parameter which now corresponds to ``event_based``.::

	[general]
	description = A demo OpenQuake-engine .ini file for event based PSHA
	calculation_mode = event_based
	random_seed = 1024

**Event based parameters**

This section is used to specify the number of stochastic event sets to be generated for each logic tree realisation 
(each stochastic event set represents a potential realisation of seismicity during the ``investigation_time`` specified 
in the ``calculation_configuration`` part). Additionally, in this section the user can specify the spatial correlation 
model to be used for the generation of ground motion fields.::

	ses_per_logic_tree_path = 5
	ground_motion_correlation_model = JB2009
	ground_motion_correlation_params = {"vs30_clustering": True}

The acceptable flags for the parameter ``vs30_clustering`` are ``False`` and ``True``, with a capital ``F`` and ``T`` 
respectively. ``0`` and ``1`` are also acceptable flags.

**Output**

This part substitutes the ``Output`` part described in the configuration file example described in the Section :ref:`Classical 
PSHA <classical-psha>`.::

	[output]
	export_dir = /tmp/xxx
	ground_motion_fields = true
	# post-process ground motion fields into hazard curves,
	# given the specified `intensity_measure_types_and_levels`
	hazard_curves_from_gmfs = true
	mean = true
	quantiles = 0.15, 0.50, 0.85
	poes = 0.1, 0.2

Starting from OpenQuake engine v2.2, it is now possible to export information about the ruptures directly in CSV format.

The option ``hazard_curves_from_gmfs`` instructs the user to use the event- based ground motion values to provide hazard 
curves indicating the probabilities of exceeding the intensity measure levels set previously in the ``intensity_measure_types_and_levels`` 
option.

***************
Scenario Hazard
***************

In order to run this calculator, the parameter ``calculation_mode`` needs to be set to ``scenario``. The user can run 
scenario calculations with and without conditioning the ground shaking to station and macroseismic data. The ground 
motion fields will be computed at each of the sites and for each of the intensity measure types specified in the job 
configuration file.

The basic job configuration file required for running a scenario hazard calculation is shown in the listing below.::

	[general]
	description = Scenario Hazard Config File
	calculation_mode = scenario

	[sites]
	sites_csv = sites.csv

	[station_data]
	station_data_file = stationlist.csv

	[rupture]
	rupture_model_file = rupture_model.xml
	rupture_mesh_spacing = 2.0

	[site_params]
	site_model_file = site_model.csv site_model_stations.csv

	[correlation]
	ground_motion_correlation_model = JB2009
	ground_motion_correlation_params = {"vs30_clustering": True}

	[hazard_calculation]
	intensity_measure_types = PGA, SA(0.3), SA(1.0)
	random_seed = 42
	truncation_level = 3.0
	maximum_distance = 200.0
	gsim = BooreAtkinson2008
	number_of_ground_motion_fields = 1000

Most of the job configuration parameters required for running a scenario hazard calculation seen in the example in the 
listing above are the same as those described in the previous sections for the classical PSHA calculator 
(Section :ref:`Classical PSHA <classical-psha>`) and the event-based PSHA calculator (Section :ref:`Event based PSHA <event-based-psha>`). The set of sites at which the 
ground motion fields will be produced can be specifed by using the ``sites`` or ``sites_csv`` parameters, or the ``region`` 
and ``region_grid_spacing`` parameters, similar to the classical PSHA and event-based PSHA calculators; other options include 
the definition of the sites through the ``site_model_file`` or the exposure model (see Section :ref:`Exposure Models <exposure-models>`).

The parameters unique to the scenario calculator are described below:

- ``number_of_ground_motion_fields``: this parameter is used to specify the number of Monte Carlo simulations of the ground motion values at the specified sites.
- ``station_data_file``: this is an optional parameter used to specify the observed intensity values for one or more intensity measure types at a set of ground motion recording stations. See example file in Table 2.1.
- ``gsim``: this parameter indicates the name of a ground motion prediction equation. Note: There are other option to indicate the ground motion models, see the sections below.

Note that each of the GSIMs specified for a conditioned GMF calculation must provide the within-event and between-event 
standard deviations separately. If a GSIM of interest provides only the total standard deviation, a (non-ideal) 
workaround might be for the user to specify the ratio between the within-event and between-event standard deviations, 
which the engine will use to add the between and within standard deviations to the GSIM.

**Station data csv file** This csv file contains the observed intensity values available from ground motion recordings 
and macroseismic intensity data. One or multiple intensity measure types can be indicated for all observations. An 
example of such a file is shown below in :ref:`the table below <example-station-data-csv>`.

When conditiong the ground motion fields to station data, all of the site parameters required by the GMMs will also need 
to be provided for the set of sites in the station_data_file. This is specified in the configuration file by including 
in the ``site_model_file`` section a ``site_model_stations.csv`` file.

.. _example-station-data-csv:
.. table:: Example of station data csv file

   +------------------+------------------+---------------+--------------+------------------+---------------+------------------+-------------------+----------------------+-------------------+----------------------+
   |  **STATION ID**  | **STATION_NAME** | **LONGITUDE** | **LATITUDE** | **STATION_TYPE** | **PGA_VALUE** | **PGA_LN_SIGMA** | **SA(0.3)_VALUE** | **SA(0.3)_LN_SIGMA** | **SA(1.0)_VALUE** | **SA(1.0)_LN_SIGMA** |
   +==================+==================+===============+==============+==================+===============+==================+===================+======================+===================+======================+
   |       VIGA       |     LAS VIGAS    |   -99.23326   |    16.7587   |      seismic     |     0.355     |        0         |       0.5262      |          0           |       0.1012      |          0           | 
   +------------------+------------------+---------------+--------------+------------------+---------------+------------------+-------------------+----------------------+-------------------+----------------------+
   |       VNTA       |     LA VENTA     |   -99.81885   |   16.91426   |      seismic     |     0.2061    |        0         |       0.3415      |          0           |       0.1051      |          0           |
   +------------------+------------------+---------------+--------------+------------------+---------------+------------------+-------------------+----------------------+-------------------+----------------------+
   |       COYC       |      COYUCA      |   -100.08996  |   16.99778   |      seismic     |     0.1676    |        0         |       0.2643      |          0           |       0.0872      |          0           |
   +------------------+------------------+---------------+--------------+------------------+---------------+------------------+-------------------+----------------------+-------------------+----------------------+
   |  UTM_14Q_041_186 |        NA        |    -99.7982   |   16.86687   |    macroseismic  |     0.6512    |      0.8059      |       0.9535      |        1.0131        |       0.4794      |        1.0822        |
   +------------------+------------------+---------------+--------------+------------------+---------------+------------------+-------------------+----------------------+-------------------+----------------------+
   |  UTM_14Q_041_185 |        NA        |    -99.79761  |   16.77656   |    macroseismic  |     0.5797    |      0.8059      |       0.8766      |        1.0131        |       0.4577      |        1.0822        |
   +------------------+------------------+---------------+--------------+------------------+---------------+------------------+-------------------+----------------------+-------------------+----------------------+
   |  UTM_14Q_040_186 |        NA        |    -99.89182  |   16.86655   |    macroseismic  |     0.477     |      0.8059      |        0.722      |        1.0131        |       0.3223      |        1.0822        |
   +------------------+------------------+---------------+--------------+------------------+---------------+------------------+-------------------+----------------------+-------------------+----------------------+

The following parameters are mandatory:

- ``STATION_ID``: string; subject to the same validity checks as the ``id`` fields in other input files.
- ``LONGITUDE``, ``LATITUDE``: floats; valid longitude and latitude values.
- ``STATION_TYPE``: string; currently the only two valid options are ‘seismic’ and ‘macroseismic’.
- ``<IMT>_VALUE``, ``<IMT>_LN_SIGMA``, ``<IMT>_STDDEV``: floats; for each IMT observed at the recording stations, two values should be provided
	
  - for IMTs that are assumed to be lognormally distributed (eg. PGV, PGA, SA), these would be the median and lognormal standard deviation using the column headers ``<IMT>_VALUE``, ``<IMT>_LN_SIGMA`` respectively.
  - for other IMTs (e.g., MMI), these would simply be the mean and standard deviation using the column headers ``<IMT>_VALUE``, ``<IMT>_STDDEV`` respectively.

The following parameters are optional:

- ``STATION_NAME``: string; free form and not subject to the same constraints as the ``STATION_ID`` field. The optional ``STATION_NAME`` field can contain information that aids in identifying a particular station.
- Other fields: could contain notes about the station, flags indicating outlier status for the values reported by the station, site information, etc., but these optional fields will not be read by the station_data_file parser.

**Ground motion models** The user can choose to specify one or multiple GSIMs (or GMPEs) for the scenario calculation using any of the options below. A list of available GSIMs can be obtained using ``oq info gsims`` in the terminal, and these are also documented at http://docs.openquake.org/oq-engine/stable/openquake.hazardlib.gsim.html.

- A single ground motion model, e.g., gsim = ``BooreAtkinson2008``.
- A GSIM logic tree (see Section :ref:`The Ground Motion Logic Tree <gm-logic-tree>`). In this case multiple ground motion models can be specified in a GMPE logic tree file using the parameter ``gsim_logic_tree_file``. In this case, the OpenQuake engine generates ground motion fields for all GMPEs specified in the logic tree file. The *Branch* weights in the logic tree file are ignored in a scenario analysis and only the individual *Branch* results are computed. Mean or quantile ground motion fields will not be generated.
- A weighted average GSIM: starting from OpenQuake engine v3.8 it is possible to indicate an AvgGMPE that computes the geometric mean of the underlying GMPEs, similarly to AvgSA. In the configuration file, a weighted average GSIM can be specified as ``gsim_logic_tree_file = gsim_weighted_avg.xml``, where the file ``gsim_weighted_avg.xml`` can be constructed using the modifiable GMPE structure for AvgGMPE as shown in the example below::

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.4">
	<logicTree logicTreeID='lt1'>
	   <logicTreeBranchingLevel branchingLevelID="bl1">
	      <logicTreeBranchSet
	      branchSetID="bs1"
	      uncertaintyType="gmpeModel"
	      applyToTectonicRegionType="Active Shallow Crust">
	      <logicTreeBranch branchID="br1">
	         <uncertaintyModel>
	            [AvgGMPE]
	            b1.AbrahamsonEtAl2014.weight=0.22
	            b2.BooreEtAl2014.weight=0.22
	            b3.CampbellBozorgnia2014.weight=0.22
	            b4.ChiouYoungs2014.weight=0.22
	            b5.Idriss2014.weight=0.12
	         </uncertaintyModel>
	         <uncertaintyWeight>
	            1.0
	         </uncertaintyWeight>
	      </logicTreeBranch>
	      </logicTreeBranchSet>
	   </logicTreeBranchingLevel>
	</logicTree>
	</nrml>