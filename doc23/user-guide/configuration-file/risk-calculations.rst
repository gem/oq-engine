Risk Calculations
-----------------

This Chapter summarises the structure of the information necessary to define the different input data to be used with 
the OpenQuake engine risk calculators. Input data for scenario-based and probabilistic seismic damage and risk analysis 
using the OpenQuake engine are organised into:

- An exposure model file in the NRML format, as described in Section :ref:`Exposure Models <exposure-models>`.
- A file describing the *Vulnerability Model* (Section :ref:`Vulnerability Models <vulnerability-models>`) for loss calculations, or a file describing the *Fragility Model* (Section :ref:`Fragility Models <fragility-models>`) for damage calculations. Optionally, a file describing the *Consequence Model* (Section :ref:`Consequence Models <consequence-models>`) can also be provided in order to calculate losses from the estimated damage distributions.
- A general calculation configuration file.
- Hazard inputs. These include hazard curves for the classical probabilistic damage and risk calculators, ground motion fields for the scenario damage and risk calculators, or stochastic event sets for the probabilistic event based calculators. As of OpenQuake engine v2.1, in general, there are five different ways in which hazard calculation parameters or results can be provided to the OpenQuake engine in order to run the subsequent risk calculations:
  
  - Use a single configuration file for running the hazard and risk calculations sequentially (preferred)
  - Use separate configuration files for running the hazard and risk calculations sequentially (legacy)
  - Use a configuration file for the risk calculation along with all hazard outputs from a previously completed, compatible OpenQuake engine hazard calculation
  - Use a configuration file for the risk calculation along with hazard input files in the OpenQuake NRML format

The file formats for *Exposure models*, *Fragility Models*, *Consequence Models*, and *Vulnerability models* have been 
described earlier in Chapter :ref:`Risk Input Models <input-models>`. The configuration file is the primary file that provides the OpenQuake 
engine information regarding both the definition of the input models (e.g. exposure, site parameters, fragility, 
consequence, or vulnerability models) as well as the parameters governing the risk calculation.

Information regarding the configuration file for running hazard calculations using the OpenQuake engine can be found in 
Section :ref:`Configuration file <configuration-file>`. Some initial mandatory parameters of the configuration file common to all of the risk 
calculators are presented in the listing. The remaining parameters that are specific to each risk calculator are 
discussed in subsequent sections.::

	[general]
	description = Example risk calculation
	calculation_mode = scenario_risk
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[vulnerability]
	structural_vulnerability_file = structural_vulnerability_model.xml

- ``description``: a parameter that can be used to include some information about the type of calculations that are going to be performed.
- ``calculation_mode``: this parameter specifies the type of calculation to be run. Valid options for the calculation_mode for the risk calculators are: scenario_damage, scenario_risk, classical_damage, classical_risk, event_based_risk, and classical_bcr.
- ``exposure_file``: this parameter is used to specify the path to the Exposure Model file. Typically this is the path to the xml file containing the exposure, or the xml file containing the metadata sections for the case where the assets are listed in one or more csv files. For particularly large exposure models, it may be more convenient to provide the path to a single compressed zip file that contains the exposure xml file and the exposure csv files (if any).

Depending on the type of risk calculation, other parameters besides the aforementioned ones may need to be provided. We 
illustrate in the following sections different examples of the configuration file for the different risk calculators.

.. _scenario-damage-calculator:

**************************
Scenario Damage Calculator
**************************

For this calculator, the parameter ``calculation_mode`` should be set to ``scenario_damage``.

**Example 1**

This example illustrates a scenario damage calculation which uses a single configuration file to first compute the 
ground motion fields for the given rupture model and then calculate damage distribution statistics based on the ground 
motion fields. A minimal job configuration file required for running a scenario damage calculation is shown in the 
listing below.::

	[general]
	description = Scenario damage using a single config file
	calculation_mode = scenario_damage
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[rupture]
	rupture_model_file = rupture_model.xml
	rupture_mesh_spacing = 2.0
	
	[site_params]
	site_model_file = site_model.xml
	
	[hazard_calculation]
	random_seed = 42
	truncation_level = 3.0
	maximum_distance = 200.0
	gsim = BooreAtkinson2008
	number_of_ground_motion_fields = 1000
	
	[fragility]
	structural_fragility_file = structural_fragility_model.xml

The general parameters ``description`` and ``calculation_mode``, and ``exposure_file`` have already been described earlier. 
The other parameters seen in the above example configuration file are described below:

- ``rupture_model_file``: a parameter used to define the path to the earthquake Rupture Model file describing the scenario event.
- ``rupture_mesh_spacing``: a parameter used to specify the mesh size (in km) used by the OpenQuake engine to discretize the rupture. Note that the smaller the mesh spacing, the greater will be (1) the precision in the calculation and (2) the computational demand.
- ``structural_fragility_file``: a parameter used to define the path to the structural Fragility Model file.

In this case, the ground motion fields will be computed at each of the locations of the assets in the exposure model. 
Ground motion fields will be generated for each of the intensity measure types found in the provided set of fragility 
models. The above calculation can be run using the command line::

	user@ubuntu:~$ oq engine --run job.ini

After the calculation is completed, a message similar to the following will be displayed::

	Calculation 2680 completed in 13 seconds. Results:
	  id | name
	5069 | Average Asset Damages

Note that one or more of the following parameters can be used in the same job configuration file to provide the 
corresponding fragility model files:

- structural_fragility_file: a parameter used to define the path to a structural Fragility Model file
- nonstructural_fragility_file: a parameter used to define the path to a nonstructural Fragility Model file
- contents_fragility_file: a parameter used to define the path to a contents Fragility Model file
- business_interruption_fragility_file: a parameter used to define the path to a business interruption Fragility Model file

It is important that the ``lossCategory`` parameter in the metadata section for each provided fragility model file 
(“structural”, “nonstructural”, “contents”, or “business_interruption”) should match the loss type defined in the 
configuration file by the relevant keyword above.

**Example 2**

This example illustrates a scenario damage calculation which uses separate configuration files for the hazard and risk 
parts of a scenario damage assessment. The first configuration file shown in the first listing below contains input 
models and parameters required for the computation of the ground motion fields due to a given rupture. The second 
configuration file shown in the second listing contains input models and parameters required for the calculation of the 
damage distribution for a portfolio of assets due to the ground motion fields.

**Scenario hazard example**::

	[general]
	description = Scenario hazard example
	calculation_mode = scenario
	
	[rupture]
	rupture_model_file = rupture_model.xml
	rupture_mesh_spacing = 2.0
	
	[sites]
	sites_csv = sites.csv
	
	[site_params]
	site_model_file = site_model.xml
	
	[hazard_calculation]
	random_seed = 42
	truncation_level = 3.0
	maximum_distance = 200.0
	gsim = BooreAtkinson2008
	intensity_measure_types = PGA, SA(0.3)
	number_of_ground_motion_fields = 1000
	ground_motion_correlation_model = JB2009
	ground_motion_correlation_params = {"vs30_clustering": True}

**Scenario damage example**::

	[general]
	description = Scenario damage example
	calculation_mode = scenario_damage
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[boundaries]
	region = -123.0 38.3, -121.0 38.3, -121.0 36.5, -123.0 36.5
	
	[hazard]
	asset_hazard_distance = 20
	
	[fragility]
	structural_fragility_file = structural_fragility_model.xml
	
	[risk_calculation]
	time_event = night

In this example, the set of intensity measure types for which the ground motion fields should be generated is specified 
explicitly in the configuration file using the parameter ``intensity_measure_types``. If the hazard calculation outputs 
are intended to be used as inputs for a subsequent scenario damage or risk calculation, the set of intensity measure 
types specified here must include all intensity measure types that are used in the fragility or vulnerability models for 
the subsequent damage or risk calculation.

In the hazard configuration file illustrated above, the list of sites at which the ground motion values will be computed 
is provided in a CSV file, specified using the ``sites_csv`` parameter. The sites used for the hazard calculation need 
not be the same as the locations of the assets in the exposure model used for the following risk calculation. In such 
cases, it is recommended to set a reasonable search radius (in km) using the ``asset_hazard_distance`` parameter for the 
OpenQuake engine to look for available hazard values, as shown in the job_damage.ini example file above.

The only new parameters introduced in the risk configuration file for this example are the ``region``, 
``asset_hazard_distance``, and ``time_event`` parameters, which are described below; all other parameters have already 
been described in earlier examples.

- ``region``: this is an optional parameter which defines the polygon that will be used for filtering the assets from the exposure model. Assets outside of this region will not be considered in the risk calculations. This region is defined using pairs of coordinates that indicate the vertices of the polygon, which should be listed in the Well-known text (WKT) format: 

  region = lon_1 lat_1, lon_2 lat_2, …, lon_n lat_n

  For each point, the longitude is listed first, followed by the latitude, both in decimal degrees. The list of points defining the polygon can be provided either in a clockwise or counter-clockwise direction.

  If the ``region`` is not provided, all assets in the exposure model are considered for the risk calculation.

  This parameter is useful in cases where the exposure model covers a region larger than the one that is of interest in the current calculation.

- ``asset_hazard_distance``: this parameter indicates the maximum allowable distance between an asset and the closest hazard input. Hazard inputs can include hazard curves or ground motion intensity values. If no hazard input site is found within the radius defined by the ``asset_hazard_distance``, the asset is skipped and a message is provided mentioning the id of the asset that is affected by this issue.

  If multiple hazard input sites are found within the radius defined by the this parameter, the hazard input site with the shortest distance from the asset location is associated with the asset. It is possible that the associated hazard input site might be located outside the polygon defined by the region.

- ``time_event``: this parameter indicates the time of day at which the event occurs. The values that this parameter can be set to are currently limited to one of the three strings: ``day``, ``night``, and ``transit``. This parameter will be used to compute the number of fatalities based on the number of occupants present in the various assets at that time of day, as specified in the exposure model.

Now, the above calculations described by the two configuration files “job_hazard.ini” and “job_damage.ini” can be run 
separately. The calculation id for the hazard calculation should be provided to the OpenQuake engine while running the 
risk calculation using the option ``--hazard-calculation-id`` (or ``--hc``). This is shown below::

	oq engine --run job_hazard.ini

After the hazard calculation is completed, a message similar to the one below will be displayed in the terminal::

	Calculation 2681 completed in 4 seconds. Results:
	  id | name
	5072 | Ground Motion Fields

In the example above, the calculation id of the hazard calculation is 2681. There is only one output from this 
calculation, i.e., the Ground Motion Fields.

The risk calculation for computing the damage distribution statistics for the portfolio of assets can now be run using::

	oq engine --run job_damage.ini --hc 2681

After the calculation is completed, a message similar to the one listed above in Example 1 will be displayed.

In order to retrieve the calculation id of a previously run hazard calculation, the option ``--list-hazard-calculations`` 
(or ``--lhc``) can be used to display a list of all previously run hazard calculations::

	job_id |     status |         start_time |         description
	  2609 | successful | 2015-12-01 14:14:14 | Mid Nepal earthquake
	  ...
	  2681 | successful | 2015-12-12 10:00:00 | Scenario hazard example

The option ``--list-outputs`` (or ``--lo``) can be used to display a list of all outputs generated during a particular 
calculation. For instance,::

	oq engine --lo 2681

will produce the following display::

	  id | name
	5072 | Ground Motion Fields

**Example 3**

The example shown in the listing below illustrates a scenario damage calculation which uses a file listing a precomputed 
set of Ground Motion Fields. These Ground Motion Fields can be computed using the OpenQuake engine or some other software. 
The Ground Motion Fields must be provided in either the Natural hazards’ Risk Markup Language schema or the csv format 
as presented in Section Outputs from Scenario Hazard Analysis. The damage distribution is computed based on the provided 
Ground Motion Fields.::

	[general]
	description = Scenario damage using user-defined ground motion fields (NRML)
	calculation_mode = scenario_damage
	
	[hazard]
	gmfs_file = gmfs.xml
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[fragility]
	structural_fragility_file = structural_fragility_model.xml

- ``gmfs_file``: a parameter used to define the path to the Ground Motion Fields file in the Natural hazards’ Risk Markup Language schema. This file must define Ground Motion Fields for all of the intensity measure types used in the Fragility Model.

The listing below shows an example of a Ground Motion Fields file in the Natural hazards’ Risk Markup Language schema 
and :ref:`this table <gmf-csv>` shows an example of a Ground Motion Fields file in the csv format. If the Ground Motion Fields file is 
provided in the csv format, an additional csv file listing the site ids must be provided using the parameter ``sites_csv``. 
See :ref:`this table <sites-csv>` for an example of the sites csv file, which provides the association between the site ids in the 
Ground Motion Fields csv file with their latitude and longitude coordinates.::

	[general]
	description = Scenario damage using user-defined ground motion fields (CSV)
	calculation_mode = scenario_damage
	
	[hazard]
	sites_csv = sites.csv
	gmfs_csv = gmfs.csv
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[fragility]
	structural_fragility_file = structural_fragility_model.xml

- ``gmfs_csv``: a parameter used to define the path to the Ground Motion Fields file in the csv format. This file must define Ground Motion Fields for all of the intensity measure types used in the Fragility Model. (`Download an example file here <https://raw.githubusercontent.com/gem/oq-engine/master/doc/manual/input_scenario_gmfs.csv>`__).
- ``sites_csv``: a parameter used to define the path to the sites file in the csv format. This file must define site id, longitude, and latitude for all of the sites for the Ground Motion Fields file provided using the gmfs_csv parameter. (`Download an example file here <https://raw.githubusercontent.com/gem/oq-engine/master/doc/manual/input_scenario_sites.csv>`_).

The above calculation(s) can be run using the command line::

	oq engine --run job.ini

**Example 4**

This example illustrates a the hazard job configuration file for a scenario damage calculation which uses two Ground 
Motion Prediction Equations instead of only one. Currently, the set of Ground Motion Prediction Equations to be used for 
a scenario calculation can be specified using a logic tree file, as demonstrated in :ref:`The Ground Motion Logic Tree <gm-logic-tree>`. As of 
OpenQuake engine v1.8, the weights in the logic tree are ignored, and a set of Ground Motion Fields will be generated for 
each Ground Motion Prediction Equation in the logic tree file. Correspondingly, damage distribution statistics will be 
generated for each set of Ground Motion Field.

The file shown in the listing below lists the two Ground Motion Prediction Equations to be used for the hazard 
calculation::

	<?xml version="1.0" encoding="UTF-8"?>
	<nrml xmlns:gml="http://www.opengis.net/gml"
	      xmlns="http://openquake.org/xmlns/nrml/0.5">
	
	<logicTree logicTreeID="lt1">
	    <logicTreeBranchSet uncertaintyType="gmpeModel"
	                        branchSetID="bs1"
	                        applyToTectonicRegionType="Active Shallow Crust">
	
	      <logicTreeBranch branchID="b1">
	        <uncertaintyModel>BooreAtkinson2008</uncertaintyModel>
	        <uncertaintyWeight>0.75</uncertaintyWeight>
	      </logicTreeBranch>
	
	      <logicTreeBranch branchID="b2">
	        <uncertaintyModel>ChiouYoungs2008</uncertaintyModel>
	        <uncertaintyWeight>0.25</uncertaintyWeight>
	      </logicTreeBranch>
	
	    </logicTreeBranchSet>
	</logicTree>
	
	</nrml>

The only change that needs to be made in the hazard job configuration file is to replace the ``gsim`` parameter with 
``gsim_logic_tree_file``, as demonstrated in the listing below.::

	[general]
	description = Scenario hazard example using multiple GMPEs
	calculation_mode = scenario
	
	[rupture]
	rupture_model_file = rupture_model.xml
	rupture_mesh_spacing = 2.0
	
	[sites]
	sites_csv = sites.csv
	
	[site_params]
	site_model_file = site_model.xml
	
	[hazard_calculation]
	random_seed = 42
	truncation_level = 3.0
	maximum_distance = 200.0
	gsim_logic_tree_file = gsim_logic_tree.xml
	intensity_measure_types = PGA, SA(0.3)
	number_of_ground_motion_fields = 1000
	ground_motion_correlation_model = JB2009
	ground_motion_correlation_params = {"vs30_clustering": True}

**Example 5**

This example illustrates a scenario damage calculation which specifies fragility models for calculating damage to 
structural and nonstructural components of structures, and also specifies *Consequence Model* files for calculation of the 
corresponding losses.

A minimal job configuration file required for running a scenario damage calculation followed by a consequences analysis 
is shown in the listing below.::

	[general]
	description = Scenario damage and consequences
	calculation_mode = scenario_damage
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[rupture]
	rupture_model_file = rupture_model.xml
	rupture_mesh_spacing = 2.0
	
	[site_params]
	site_model_file = site_model.xml
	
	[hazard_calculation]
	random_seed = 42
	truncation_level = 3.0
	maximum_distance = 200.0
	gsim = BooreAtkinson2008
	number_of_ground_motion_fields = 1000
	ground_motion_correlation_model = JB2009
	ground_motion_correlation_params = {"vs30_clustering": True}
	
	[fragility]
	structural_fragility_file = structural_fragility_model.xml
	nonstructural_fragility_file = nonstructural_fragility_model.xml
	
	[consequence]
	structural_consequence_file = structural_consequence_model.xml
	nonstructural_consequence_file = nonstructural_consequence_model.xml

Note that one or more of the following parameters can be used in the same job configuration file to provide the 
corresponding *Consequence Model* files:

- ``structural_consequence_file``: a parameter used to define the path to a structural Consequence Model file
- ``nonstructural_consequence_file``: a parameter used to define the path to a nonstructural Consequence Model file
- ``contents_consequence_file``: a parameter used to define the path to a contents Consequence Model file
- ``business_interruption_consequence_file``: a parameter used to define the path to a business interruption Consequence Model file

It is important that the ``lossCategory`` parameter in the metadata section for each provided Consequence Model file 
(“structural”, “nonstructural”, “contents”, or “business_interruption”) should match the loss type defined in the 
configuration file by the relevant keyword above.

The above calculation can be run using the command line::

	user@ubuntu:~$ oq engine --run job.ini

After the calculation is completed, a message similar to the following will be displayed::

	Calculation 1579 completed in 37 seconds. Results:
	  id | name
	8990 | Average Asset Losses
	8993 | Average Asset Damages

.. _scenario-risk-calculator:

************************
Scenario Risk Calculator
************************

In order to run this calculator, the parameter ``calculation_mode`` needs to be set to ``scenario_risk``.

Most of the job configuration parameters required for running a scenario risk calculation are the same as those described 
in the previous section for the scenario damage calculator. The remaining parameters specific to the scenario risk 
calculator are illustrated through the examples below.

**Example 1**

This example illustrates a scenario risk calculation which uses a single configuration file to first compute the ground 
motion fields for the given rupture model and then calculate loss statistics for structural losses and nonstructural 
losses, based on the ground motion fields. The job configuration file required for running this scenario risk calculation 
is shown in the listing below.::

	[general]
	description = Scenario risk using a single config file
	calculation_mode = scenario_risk
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[rupture]
	rupture_model_file = rupture_model.xml
	rupture_mesh_spacing = 2.0
	
	[site_params]
	site_model_file = site_model.xml
	
	[hazard_calculation]
	random_seed = 42
	truncation_level = 3.0
	maximum_distance = 200.0
	gsim = BooreAtkinson2008
	number_of_ground_motion_fields = 1000
	ground_motion_correlation_model = JB2009
	ground_motion_correlation_params = {"vs30_clustering": True}
	
	[vulnerability]
	structural_vulnerability_file = structural_vulnerability_model.xml
	nonstructural_vulnerability_file = nonstructural_vulnerability_model.xml
	
	[risk_calculation]
	master_seed = 24
	asset_correlation = 1

Whereas a scenario damage calculation requires one or more fragility and/or consequence models, a scenario risk 
calculation requires the user to specify one or more vulnerability model files. Note that one or more of the following 
parameters can be used in the same job configuration file to provide the corresponding vulnerability model files:

- ``structural_vulnerability_file``: this parameter is used to specify the path to the structural *Vulnerability Model* file
- ``nonstructural_vulnerability_file``: this parameter is used to specify the path to the nonstructuralvulnerabilitymodel file
- ``contents_vulnerability_file``: this parameter is used to specify the path to the contents *Vulnerability Model* file
- ``business_interruption_vulnerability_file``: this parameter is used to specify the path to the business interruption *Vulnerability Model* file
- ``occupants_vulnerability_file``: this parameter is used to specify the path to the occupants *Vulnerability Model* file

It is important that the ``lossCategory`` parameter in the metadata section for each provided vulnerability model file 
(“structural”, “nonstructural”, “contents”, “business_interruption”, or “occupants”) should match the loss type defined 
in the configuration file by the relevant keyword above.

The remaining new parameters introduced in this example are the following:

- ``master_seed``: this parameter is used to control the random number generator in the loss ratio sampling process. If the same ``master_seed`` is defined at each calculation run, the same random loss ratios will be generated, thus allowing reproducibility of the results.
- ``asset_correlation``: if the uncertainty in the loss ratios has been defined within the *Vulnerability Model*, users can specify a coefficient of correlation that will be used in the Monte Carlo sampling process of the loss ratios, between the assets that share the same taxonomy. If the ``asset_correlation`` is set to one, the loss ratio residuals will be perfectly correlated. On the other hand, if this parameter is set to zero, the loss ratios will be sampled independently. If this parameter is not defined, the OpenQuake engine will assume zero correlation in the vulnerability. As of OpenQuake engine v1.8, ``asset_correlation`` applies only to continuous vulnerabilityfunctions using the lognormal or Beta distribution; it does not apply to vulnerability functions defined using the PMF distribution. Although partial correlation was supported in previous versions of the engine, beginning from OpenQuake engine v2.2, values between zero and one are no longer supported due to performance considerations. The only two values permitted are ``asset_correlation = 0`` and ``asset_correlation = 1``.

In this case, the ground motion fields will be computed at each of the locations of the assets in the exposure model and 
for each of the intensity measure types found in the provided set of vulnerability models. The above calculation can be 
run using the command line::

	user@ubuntu:~$ oq engine --run job.ini

After the calculation is completed, a message similar to the following will be displayed::

	Calculation 2735 completed in 10 seconds. Results:
	  id | name
	5328 | Aggregate Asset Losses
	5329 | Average Asset Losses
	5330 | Aggregate Event Losses

All of the different ways of running a scenario damage calculation as illustrated through the examples of the previous 
section are also applicable to the scenario risk calculator, though the examples are not repeated here.

A few additional parameters related to the event based risk calculator that may be useful for controlling specific 
aspects of the calculation are listed below:

- ``ignore_covs``: this parameter controls the propagation of vulnerability uncertainty to losses. The vulnerability functions using continuous distributions (such as the lognormal distribution or beta distribution) to characterize the uncertainty in the loss ratio conditional on the shaking intensity level, specify the mean loss ratios and the corresponding coefficients of variation for a set of intensity levels. They are used to build the so called *Epsilon* matrix within the engine, which is how loss ratios are sampled from the distribution for each asset. There is clearly a performance penalty associated with the propagation of uncertainty in the vulnerability to losses. The *Epsilon* matrix has to be computed and stored, and then the worker processes have to read it, which involves large quantities of data transfer and memory usage. Setting ``ignore_covs = true`` in the job file will result in the engine using just the mean loss ratio conditioned on the shaking intensity and ignoring the uncertainty. This tradeoff of not propagating the vulnerabilty uncertainty to the loss estimates can lead to a significant boost in performance and tractability. The default value of ``ignore_covs`` is ``false``.

.. _classical-psd-calculator:

*************************************************
Classical Probabilistic Seismic Damage Calculator
*************************************************

In order to run this calculator, the parameter ``calculation_mode`` needs to be set to ``classical_damage``.

Most of the job configuration parameters required for running a classical probabilistic damage calculation are the same 
as those described in the section for the scenario damage calculator. The remaining parameters specific to the classical 
probabilistic damage calculator are illustrated through the examples below.

**Example 1**

This example illustrates a classical probabilistic damage calculation which uses a single configuration file to first 
compute the hazard curves for the given source model and ground motion model and then calculate damage distribution 
statistics based on the hazard curves. A minimal job configuration file required for running a classical probabilistic 
damage calculation is shown in the listing below.::

	[general]
	description = Classical probabilistic damage using a single config file
	calculation_mode = classical_damage
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[erf]
	width_of_mfd_bin = 0.1
	rupture_mesh_spacing = 2
	area_source_discretization = 20
	
	[site_params]
	site_model_file = site_model.xml
	
	[logic_trees]
	source_model_logic_tree_file = source_model_logic_tree.xml
	gsim_logic_tree_file = gsim_logic_tree.xml
	number_of_logic_tree_samples = 0
	
	[hazard_calculation]
	random_seed = 42
	investigation_time = 1
	truncation_level = 3.0
	maximum_distance = 200.0
	
	[fragility]
	structural_fragility_file = structural_fragility_model.xml

The general parameters ``description`` and ``calculation_mode``, and ``exposure_file`` have already been described 
earlier in Section :ref:`Scenario Damage Calculator <scenario-damage-calculator>`. The parameters related to the hazard curves computation have been 
described earlier in Section :ref:`Classical PSHA <classical-psha>`.

In this case, the hazard curves will be computed at each of the locations of the assets in the exposure model, for each 
of the intensity measure types found in the provided set of fragility models. The above calculation can be run using the 
command line::

	oq engine --run job.ini

After the calculation is completed, a message similar to the following will be displayed::

	Calculation 2741 completed in 12 seconds. Results:
	  id | name
	5359 | Asset Damage Distribution

**Example 2**

This example illustrates a classical probabilistic damage calculation which uses separate configuration files for the 
hazard and risk parts of a classical probabilistic damage assessment. The first configuration file shown in the listing 
below contains input models and parameters required for the computation of the hazard curves.::

	[general]
	description = Classical probabilistic hazard
	calculation_mode = classical
	
	[sites]
	region = -123.0 38.3, -121.0 38.3, -121.0 36.5, -123.0 36.5
	region_grid_spacing = 0.5
	
	[erf]
	width_of_mfd_bin = 0.1
	rupture_mesh_spacing = 2
	area_source_discretization = 20
	
	[site_params]
	site_model_file = site_model.xml
	
	[logic_trees]
	source_model_logic_tree_file = source_model_logic_tree.xml
	gsim_logic_tree_file = gsim_logic_tree.xml
	number_of_logic_tree_samples = 0
	
	[hazard_calculation]
	random_seed = 42
	investigation_time = 1
	truncation_level = 3.0
	maximum_distance = 200.0
	intensity_measure_types_and_levels = {
	 "PGA": logscale(0.05, 3.0, 30),
	 "SA(1.0)": logscale(0.05, 3.0, 30)}

The second configuration file shown in the listing below contains input models and parameters required for the 
calculation of the probabilistic damage distribution for a portfolio of assets based on the hazard curves and fragility 
models.::

	[general]
	description = Classical probabilistic damage example
	calculation_mode = classical_damage
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[hazard]
	asset_hazard_distance = 20
	
	[fragility]
	structural_fragility_file = structural_fragility_model.xml
	
	[risk_calculation]
	risk_investigation_time = 50
	steps_per_interval = 4

Now, the above calculations described by the two configuration files “job_hazard.ini” and “job_damage.ini” can be run 
sequentially or separately, as illustrated in Example 2 in Section :ref:`Scenario Damage Calculator <scenario-damage-calculator>`. The new parameters 
introduced in the above example configuration file are described below:

- ``risk_investigation_time``: an optional parameter that can be used in probabilistic damage or risk calculations where the period of interest for the risk calculation is different from the period of interest for the hazard calculation. If this parameter is not explicitly set, the OpenQuake engine will assume that the risk calculation is over the same time period as the preceding hazard calculation.
- ``steps_per_interval``: an optional parameter that can be used to specify whether discrete fragility functions in the fragility models should be discretized further, and if so, how many intermediate steps to use for the discretization. Setting ``steps_per_interval = n`` will result in the OpenQuake engine discretizing the discrete fragility models using (n - 1) linear interpolation steps between each pair of intensity level, poe points. The default value of this parameter is one, implying no interpolation.

***********************************************
Classical Probabilistic Seismic Risk Calculator
***********************************************

In order to run this calculator, the parameter ``calculation_mode`` needs to be set to ``classical_risk``.

Most of the job configuration parameters required for running a classical probabilistic risk calculation are the same as 
those described in the previous section for the classical probabilistic damage calculator. The remaining parameters 
specific to the classical probabilistic risk calculator are illustrated through the examples below.

**Example 1**

This example illustrates a classical probabilistic risk calculation which uses a single configuration file to first 
compute the hazard curves for the given source model and ground motion model and then calculate loss exceedance curves 
based on the hazard curves. An example job configuration file for running a classical probabilistic risk calculation is 
shown in the listing below.::

	[general]
	description = Classical probabilistic risk using a single config file
	calculation_mode = classical_risk
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[erf]
	width_of_mfd_bin = 0.1
	rupture_mesh_spacing = 2
	area_source_discretization = 20
	
	[site_params]
	site_model_file = site_model.xml
	
	[logic_trees]
	source_model_logic_tree_file = source_model_logic_tree.xml
	gsim_logic_tree_file = gsim_logic_tree.xml
	number_of_logic_tree_samples = 0
	
	[hazard_calculation]
	random_seed = 42
	investigation_time = 1
	truncation_level = 3.0
	maximum_distance = 200.0
	
	[vulnerability]
	structural_vulnerability_file = structural_vulnerability_model.xml
	nonstructural_vulnerability_file = nonstructural_vulnerability_model.xml

Apart from the calculation mode, the only difference with the example job configuration file shown in Example 1 of 
Section :ref:`Classical Probabilistic Seismic Damage Calculator <classical-psd-calculator>` is the use of a vulnerability model instead of a fragility 
model.

As with the Scenario Risk calculator, it is possible to specify one or more *Vulnerability Model* files in the same job 
configuration file, using the parameters:

- ``structural_vulnerability_file``,
- ``nonstructural_vulnerability_file``,
- ``contents_vulnerability_file``,
- ``business_interruption_vulnerability_file``, and/or
- ``occupants_vulnerability_file``

It is important that the ``lossCategory`` parameter in the metadata section for each provided vulnerability model file 
(“structural”, “nonstructural”, “contents”, “business_interruption”, or “occupants”) should match the loss type defined 
in the configuration file by the relevant keyword above.

In this case, the hazard curves will be computed at each of the locations of the assets in the *Exposure Model*, for 
each of the intensity measure types found in the provided set of vulnerabilitymodels. The above calculation can be run 
using the command line::

	oq engine --run job.ini

After the calculation is completed, a message similar to the following will be displayed::

	Calculation 2749 completed in 24 seconds. Results:
	  id | name
	3980 | Asset Loss Curves Statistics
	3981 | Asset Loss Maps Statistics
	3983 | Average Asset Loss Statistics

**Example 2**

This example illustrates a classical probabilistic risk calculation which uses separate configuration files for the 
hazard and risk parts of a classical probabilistic risk assessment. The first configuration file shown in the listing 
contains input models and parameters required for the computation of the hazard curves.::

	[general]
	description = Classical probabilistic hazard
	calculation_mode = classical
	
	[sites]
	region = -123.0 38.3, -121.0 38.3, -121.0 36.5, -123.0 36.5
	region_grid_spacing = 0.5
	
	[erf]
	width_of_mfd_bin = 0.1
	rupture_mesh_spacing = 2
	area_source_discretization = 20
	
	[site_params]
	site_model_file = site_model.xml
	
	[logic_trees]
	source_model_logic_tree_file = source_model_logic_tree.xml
	gsim_logic_tree_file = gsim_logic_tree.xml
	number_of_logic_tree_samples = 0
	
	[hazard_calculation]
	random_seed = 42
	investigation_time = 1
	truncation_level = 3.0
	maximum_distance = 200.0
	intensity_measure_types_and_levels = {
	 "PGA": logscale(0.05, 3.0, 30),
	 "SA(1.0)": logscale(0.05, 3.0, 30)}

The second configuration file shown in the listing below contains input models and parameters required for the 
calculation of the loss exceedance curves and probabilistic loss maps for a portfolio of assets based on the hazard 
curves and vulnerability models.::

	[general]
	description = Classical probabilistic risk
	calculation_mode = classical_risk
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[hazard]
	asset_hazard_distance = 20
	
	[vulnerability]
	structural_vulnerability_file = structural_vulnerability_model.xml
	nonstructural_vulnerability_file = nonstructural_vulnerability_model.xml
	
	[risk_calculation]
	risk_investigation_time = 50
	lrem_steps_per_interval = 2
	
	[risk_outputs]
	quantiles = 0.15, 0.50, 0.85
	conditional_loss_poes = 0.02, 0.10

Now, the above calculations described by the two configuration files “job_hazard.ini” and “job_risk.ini” can be run 
sequentially or separately, as illustrated in Example 2 in Section :ref:`Scenario Damage Calculator <scenario-damage-calculator>`. The new parameters 
introduced in the above risk configuration file example are described below:

- ``lrem_steps_per_interval``: this parameter controls the number of intermediate values between consecutive loss ratios (as defined in the Vulnerability Model) that are considered in the risk calculations. A larger number of loss ratios than those defined in each Vulnerability Function should be considered, in order to better account for the uncertainty in the loss ratio distribution. If this parameter is not defined in the configuration file, the OpenQuake engine assumes the ``lrem_steps_per_interval`` to be equal to 5. More details are provided in the OpenQuake Book (Risk).
- ``quantiles``: this parameter can be used to request the computation of quantile loss curves for computations involving non-trivial logic trees. The quantiles for which the loss curves should be computed must be provided as a comma separated list. If this parameter is not included in the configuration file, quantile loss curves will not be computed.
- ``conditional_loss_poes``: this parameter can be used to request the computation of probabilistic loss maps, which give the loss levels exceeded at the specified probabilities of exceedance over the time period specified by ``risk_investigation_time``. The probabilities of exceedance for which the loss maps should be computed must be provided as a comma separated list. If this parameter is not included in the configuration file, probabilistic loss maps will not be computed.

*************************************
Stochastic Event Based Seismic Damage
*************************************

The parameter ``calculation_mode`` needs to be set to ``event_based_damage`` in order to use this calculator.

Most of the job configuration parameters required for running a stochastic event based damage calculation are the same 
as those described in the previous sections for the scenario damage calculator and the classical probabilistic damage 
calculator. The remaining parameters specific to the stochastic event based damage calculator are illustrated through 
the example below.

**Example 1**

This example illustrates a stochastic event based damage calculation which uses a single configuration file to first 
compute the Stochastic Event Sets and Ground Motion Fields for the given source model and ground motion model, and then 
calculate event loss tables, loss exceedance curves and probabilistic loss maps for structural losses, nonstructural 
losses and occupants, based on the Ground Motion Fields. The job configuration file required for running this stochastic 
event based damage calculation is shown in the listing below.::

	[general]
	description = Stochastic event based damage using a single job file
	calculation_mode = event_based_damage
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[site_params]
	site_model_file = site_model.xml
	
	[erf]
	width_of_mfd_bin = 0.1
	rupture_mesh_spacing = 2.0
	area_source_discretization = 10.0
	
	[logic_trees]
	source_model_logic_tree_file = source_model_logic_tree.xml
	gsim_logic_tree_file = gsim_logic_tree.xml
	number_of_logic_tree_samples = 0
	
	[correlation]
	ground_motion_correlation_model = JB2009
	ground_motion_correlation_params = {"vs30_clustering": True}
	
	[hazard_calculation]
	random_seed = 24
	truncation_level = 3
	maximum_distance = 200.0
	investigation_time = 1
	ses_per_logic_tree_path = 10000
	
	[fragility]
	structural_fragility_file = structural_fragility_model.xml
	
	[consequence]
	structural_consequence_file = structural_consequence_model.xml
	
	[risk_calculation]
	master_seed = 42
	risk_investigation_time = 1
	return_periods = 5, 10, 25, 50, 100, 250, 500, 1000

Similar to that the procedure described for the Scenario Damage calculator, a Monte Carlo sampling process is also 
employed in this calculator to take into account the uncertainty in the conditional loss ratio at a particular intensity 
level. Hence, the parameters ``asset_correlation`` and ``master_seed`` may be defined as previously described for the 
Scenario Damage calculator in Section :ref:`Scenario Damage Calculator <scenario-damage-calculator>`. The parameter ``risk_investigation_time`` specifies the 
time period for which the average damage values will be calculated, similar to the Classical Probabilistic Damage 
calculator. If this parameter is not provided in the risk job configuration file, the time period used is the same as 
that specifed in the hazard calculation using the parameter “investigation_time”.

The new parameters introduced in this example are described below:

- ``minimum_intensity``: this optional parameter specifies the minimum intensity levels for each of the intensity measure types in the risk model. Ground motion fields where each ground motion value is less than the specified minimum threshold are discarded. This helps speed up calculations and reduce memory consumption by considering only those ground motion fields that are likely to contribute to losses. It is also possible to set the same threshold value for all intensity measure types by simply providing a single value to this parameter. For instance: “minimum_intensity = 0.05” would set the threshold to 0.05 g for all intensity measure types in the risk calculation. If this parameter is not set, the OpenQuake engine extracts the minimum thresholds for each intensity measure type from the vulnerability models provided, picking the lowest intensity value for which a mean loss ratio is provided.
- ``return_periods``: this parameter specifies the list of return periods (in years) for computing the asset / aggregate damage curves. If this parameter is not set, the OpenQuake engine uses a default set of return periods for computing the loss curves. The default return periods used are from the list: [5, 10, 25, 50, 100, 250, 500, 1000, …], with its upper bound limited by ``(ses_per_logic_tree_path × investigation_time)`` 
 
.. math::

  average\_damages &= sum(event\_damages) \\
                   &{\div}\ (hazard\_investigation\_time {\times}\ ses\_per\_logic\_tree\_path) \\
                   &{\times}\ risk\_investigation\_time

The above calculation can be run using the command line::

	oq engine --run job.ini

Computation of the damage curves, and average damages for each individual asset in the *Exposure Model* can be resource 
intensive, and thus these outputs are not generated by default.

**********************************************
Stochastic Event Based Seismic Risk Calculator
**********************************************

The parameter ``calculation_mode`` needs to be set to ``event_based_risk`` in order to use this calculator.

Most of the job configuration parameters required for running a stochastic event based risk calculation are the same as 
those described in the previous sections for the scenario risk calculator and the classical probabilistic risk calculator. 
The remaining parameters specific to the stochastic event based risk calculator are illustrated through the example below.

**Example 1**

This example illustrates a stochastic event based risk calculation which uses a single configuration file to first 
compute the Stochastic Event Sets and Ground Motion Fields for the given source model and ground motion model, and then 
calculate event loss tables, loss exceedance curves and probabilistic loss maps for structural losses, nonstructural 
losses and occupants, based on the Ground Motion Fields. The job configuration file required for running this stochastic 
event based risk calculation is shown in the listing below.::

	[general]
	description = Stochastic event based risk using a single job file
	calculation_mode = event_based_risk
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[site_params]
	site_model_file = site_model.xml
	
	[erf]
	width_of_mfd_bin = 0.1
	rupture_mesh_spacing = 2.0
	area_source_discretization = 10.0
	
	[logic_trees]
	source_model_logic_tree_file = source_model_logic_tree.xml
	gsim_logic_tree_file = gsim_logic_tree.xml
	
	[correlation]
	ground_motion_correlation_model = JB2009
	ground_motion_correlation_params = {"vs30_clustering": True}
	
	[hazard_calculation]
	random_seed = 24
	truncation_level = 3
	maximum_distance = 200.0
	investigation_time = 1
	number_of_logic_tree_samples = 0
	ses_per_logic_tree_path = 100000
	minimum_intensity = {"PGA": 0.05, "SA(0.4)": 0.10, "SA(0.8)": 0.12}
	
	[vulnerability]
	structural_vulnerability_file = structural_vulnerability_model.xml
	nonstructural_vulnerability_file = nonstructural_vulnerability_model.xml
	
	[risk_calculation]
	master_seed = 42
	risk_investigation_time = 1
	asset_correlation = 0
	return_periods = [5, 10, 25, 50, 100, 250, 500, 1000]
	
	[risk_outputs]
	avg_losses = true
	quantiles = 0.15, 0.50, 0.85
	conditional_loss_poes = 0.02, 0.10

Similar to that the procedure described for the Scenario Risk calculator, a Monte Carlo sampling process is also 
employed in this calculator to take into account the uncertainty in the conditional loss ratio at a particular intensity 
level. Hence, the parameters ``asset_correlation`` and ``master_seed`` may be defined as previously described for the Scenario 
Risk calculator in Section :ref:`Scenario Risk Assessment <scenario-risk-assessment>`. The parameter ``risk_investigation_time`` specifies the time period 
for which the event loss tables and loss exceedance curves will be calculated, similar to the Classical Probabilistic 
Risk calculator. If this parameter is not provided in the risk job configuration file, the time period used is the same 
as that specifed in the hazard calculation using the parameter “investigation_time”.

The new parameters introduced in this example are described below:

- ``minimum_intensity``: this optional parameter specifies the minimum intensity levels for each of the intensity measure types in the risk model. Ground motion fields where each ground motion value is less than the specified minimum threshold are discarded. This helps speed up calculations and reduce memory consumption by considering only those ground motion fields that are likely to contribute to losses. It is also possible to set the same threshold value for all intensity measure types by simply providing a single value to this parameter. For instance: “minimum_intensity = 0.05” would set the threshold to 0.05 g for all intensity measure types in the risk calculation. If this parameter is not set, the OpenQuake engine extracts the minimum thresholds for each intensity measure type from the vulnerability models provided, picking the lowest intensity value for which a mean loss ratio is provided.
- ``return_periods``: this parameter specifies the list of return periods (in years) for computing the aggregate loss curve. If this parameter is not set, the OpenQuake engine uses a default set of return periods for computing the loss curves. The default return periods used are from the list: [5, 10, 25, 50, 100, 250, 500, 1000, …], with its upper bound limited by (ses_per_logic_tree_path × investigation_time)
- ``avg_losses``: this boolean parameter specifies whether the average asset losses over the time period “risk_investigation_time” should be computed. The default value of this parameter is true.

.. math::

  average\_loss &= sum(event\_losses) \\
                &{\div}\ (hazard\_investigation\_time {\times}\ ses\_per\_logic\_tree\_path) \\
                &{\times}\ risk\_investigation\_time

The above calculation can be run using the command line::

	user@ubuntu:$ oq engine --run job.ini

Computation of the loss tables, loss curves, and average losses for each individual asset in the *Exposure Model* can be 
resource intensive, and thus these outputs are not generated by default, unless instructed to by using the parameters 
described above.

Users may also begin an event based risk calculation by providing a precomputed set of Ground Motion Fields to the 
OpenQuake engine. The following example describes the procedure for this approach.

**Example 2**

This example illustrates a stochastic event based risk calculation which uses a file listing a precomputed set of Ground 
Motion Fields. These Ground Motion Fields can be computed using the OpenQuake engine or some other software. The Ground 
Motion Fields must be provided in the csv format as presented in Section :ref:`Event based PSHA <event-based-psha>`. Table 2.2 shows an example 
of a Ground Motion Fields file in the csv format.

An additional csv file listing the site ids must also be provided using the parameter ``sites_csv``. See Table 2.5 for 
an example of the sites csv file, which provides the association between the site ids in the Ground Motion Fields csv 
file with their latitude and longitude coordinates.

Starting from the input Ground Motion Fields, the OpenQuake engine can calculate event loss tables, loss exceedance 
curves and probabilistic loss maps for structural losses, nonstructural losses and occupants. The job configuration 
file required for running this stochastic event based risk calculation starting from a precomputed set of Ground Motion 
Fields is shown in the listing below.::

	[general]
	description = Stochastic event based risk using precomputed gmfs
	calculation_mode = event_based_risk
	
	[hazard]
	sites_csv = sites.csv
	gmfs_csv = gmfs.csv
	investigation_time = 50
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[vulnerability]
	structural_vulnerability_file = structural_vulnerability_model.xml
	
	[risk_calculation]
	risk_investigation_time = 1
	return_periods = [5, 10, 25, 50, 100, 250, 500, 1000]
	
	[risk_outputs]
	avg_losses = true
	quantiles = 0.15, 0.50, 0.85
	conditional_loss_poes = 0.02, 0.10

**Additional parameters**

A few additional parameters related to the event based risk calculator that may be useful for controlling specific 
aspects of the calculation are listed below:

- ``individual_curves``: this boolean parameter is used to specify if the asset loss curves for each *Branch* realization should be saved to the datastore. For the asset loss curves output, by default the engine only saves and exports statistical results, i.e. the mean and quantile asset loss curves. If you want the asset loss curves for each of the individual *Branch* realizations, you must set ``individual_curves=true`` in the job file. Please take care: if you have hundreds of realizations, the data transfer and disk space requirements will be orders of magnitude larger than just returning the mean and quantile asset loss curves, and the calculation might fail. The default value of ``individual_curves`` is ``false``.
- ``asset_correlation``: if the uncertainty in the loss ratios has been defined within the *Vulnerability Model*, users can specify a coefficient of correlation that will be used in the Monte Carlo sampling process of the loss ratios, between the assets that share the same taxonomy. If the ``asset_correlation`` is set to one, the loss ratio residuals will be perfectly correlated. On the other hand, if this parameter is set to zero, the loss ratios will be sampled independently. If this parameter is not defined, the OpenQuake engine will assume zero correlation in the vulnerability. As of OpenQuake engine v1.8, ``asset_correlation`` applies only to continuous vulnerabilityfunctions using the lognormal or Beta distribution; it does not apply to vulnerabilityfunctions defined using the PMF distribution. Although partial correlation was supported in previous versions of the engine, beginning from OpenQuake engine v2.2, values between zero and one are no longer supported due to performance considerations. The only two values permitted are ``asset_correlation = 0`` and ``asset_correlation = 1``.
- ``ignore_covs``: this parameter controls the propagation of vulnerability uncertainty to losses. The vulnerability functions using continuous distributions (such as the lognormal distribution or beta distribution) to characterize the uncertainty in the loss ratio conditional on the shaking intensity level, specify the mean loss ratios and the corresponding coefficients of variation for a set of intensity levels. They are used to build the so called *Epsilon* matrix within the engine, which is how loss ratios are sampled from the distribution for each asset. There is clearly a performance penalty associated with the propagation of uncertainty in the vulnerability to losses. The *Epsilon* matrix has to be computed and stored, and then the worker processes have to read it, which involves large quantities of data transfer and memory usage. Setting ``ignore_covs = true`` in the job file will result in the engine using just the mean loss ratio conditioned on the shaking intensity and ignoring the uncertainty. This tradeoff of not propagating the vulnerabilty uncertainty to the loss estimates can lead to a significant boost in performance and tractability. The default value of ``ignore_covs`` is ``false``.

**Additional exceedance probability curves**

Starting from engine v3.18, it is possible to export aggregated loss curves that consider only 
the maximum loss in a year, commonly referred to as Occurrence Exceedance Probability (OEP), 
and loss curves that consider the sum of losses in a year, commonly referred to as 
Aggregate Exceedance Probability (AEP).

OEP and AEP curves can be calculated for event-based damage and risk calculations. To do so, the configuration file, 
``job.ini``, needs to specify the parameters presented below, in addition to the parameters generally indicated for these 
type of calculations::

	[risk_calculation]
	aggregate_loss_curves_types = oep, aep

By default, all event-based damage and risk calculations include the aggregated loss curves considering each event individually (EP), corresponding with the aggregated loss curves traditionally implemented in the engine.

_NOTE:_ When the calculation includes reinsurance treaties, the reinsurance curves (aggregated loss curves for retention, 
claim, cession per treaty and overspills) are also estimated for OEP and AEP.


**************************************
Retrofit Benefit-Cost Ratio Calculator
**************************************

As previously explained, this calculator uses loss exceedance curves which are calculated using the Classical 
Probabilistic risk calculator. In order to run this calculator, the parameter ``calculation_mode`` needs to be set to 
``classical_bcr``.

Most of the job configuration parameters required for running a classical retrofit benefit-cost ratio calculation are the 
same as those described in the previous section for the classical probabilistic risk calculator. The remaining parameters 
specific to the classical retrofit benefit-cost ratio calculator are illustrated through the examples below.

**Example 1**

This example illustrates a classical probabilistic retrofit benefit-cost ratio calculation which uses a single 
configuration file to first compute the hazard curves for the given source model and ground motion model, then calculate 
loss exceedance curves based on the hazard curves using both the original vulnerability model and the vulnerability model 
for the retrofitted structures, then calculate the reduction in average annual losses due to the retrofits, and finally 
calculate the benefit-cost ratio for each asset. A minimal job configuration file required for running a classical 
probabilistic retrofit benefit-cost ratio calculation is shown in the listing below.::

	[general]
	description = Classical cost-benefit analysis using a single config file
	calculation_mode = classical_bcr
	
	[exposure]
	exposure_file = exposure_model.xml
	
	[erf]
	width_of_mfd_bin = 0.1
	rupture_mesh_spacing = 2
	area_source_discretization = 20
	
	[site_params]
	site_model_file = site_model.xml
	
	[logic_trees]
	source_model_logic_tree_file = source_model_logic_tree.xml
	gsim_logic_tree_file = gsim_logic_tree.xml
	number_of_logic_tree_samples = 0
	
	[hazard_calculation]
	random_seed = 42
	investigation_time = 1
	truncation_level = 3.0
	maximum_distance = 200.0
	
	[vulnerability]
	structural_vulnerability_file = structural_vulnerability_model.xml
	structural_vulnerability_retrofitted_file = retrofit_vulnerability_model.xml
	
	[risk_calculation]
	interest_rate = 0.05
	asset_life_expectancy = 50
	lrem_steps_per_interval = 1

The new parameters introduced in the above example configuration file are described below:

- ``vulnerability_retrofitted_file``: this parameter is used to specify the path to the Vulnerability Model file containing the vulnerabilityfunctions for the retrofitted asset
- ``interest_rate``: this parameter is used in the calculation of the present value of potential future benefits by discounting future cash flows
- ``asset_life_expectancy``: this variable defines the life expectancy or design life of the assets, and is used as the time-frame in which the costs and benefits of the retrofit will be compared

The above calculation can be run using the command line::

	user@ubuntu:~$ oq engine --run job.ini

After the calculation is completed, a message similar to the following will be displayed::

	Calculation 2776 completed in 25 seconds. Results:
	  id | name
	5422 | Benefit-cost ratio distribution | BCR Map. type=structural, hazard=5420

***************************
Reinsurance Loss Calculator
***************************

Reinsurance losses can be calculated for event-based and scenario risk calculations. To do so, the configuration file, 
``job.ini``, needs to specify the parameters presented below, in addition to the parameters generally indicated for these 
type of calculations::

	[risk_calculation]
	aggregate_by = policy
	reinsurance_file = {'structural+contents': 'reinsurance.xml'}
	total_losses = structural+contents

**Additional comments:**

- ``aggregate_by``: it is possible to define multiple aggregation keys. However, for reinsurance calculations the ``policy`` key must be present, otherwise an error message will be raised. In the following example, multiple aggregation keys are used::

	aggregate_by = policy; tag1

  In this case, aggregated loss curves will be produced also for ``tag1`` and ``policy``, while reinsurance outputs will only be produced for the policy.

- ``reinsurance_file``: This dictionary associates the reinsurance information to a given the loss_type (the engine supports structural, nonstructural, contents or its sum). The insurance and reinsurance calculations are applied over the indicated loss_types, i.e. to the sum of the ground up losses associated with the specified loss_types.

  *NOTE: The current implementation works only with a single reinsurance file.*

- ``total_losses``: (or total exposed value) needs to be specified when the reinsurance needs to be applied over the sum of two or more loss types (e.g. ``structural+contents``). The definition of total losses is also reflected in the risk outputs of the calculation. NB: if there is a single loss type (e.g. ``structural``) there is no need to specify this parameter, just write ``reinsurance_file = {'structural': 'reinsurance.xml'}``


Using ``collect_rlzs=true`` in the risk calculation
---------------------------------------------------

Since version 3.12 the engine recognizes a flag ``collect_rlzs`` in the risk configuration file. When the flag is set 
to true, then the hazard realizations are collected together when computing the risk results and considered as one.

Setting ``collect_rlzs=true`` is possible only when the weights of the realizations are all equal, otherwise, the engine 
raises an error. Collecting the realizations makes the calculation of the average losses and loss curves much faster 
and more memory efficient. It is the recommended way to proceed when you are interested only in mean results. When you 
have a large exposure and many realizations (say 5 million assets and 1000 realizations, as it is the case for Chile) 
setting ``collect_rlzs=true`` can make possible a calculation that otherwise would run out of memory.

Note 1: when using sampling, ``collect_rlzs`` is implicitly set to ``True``, so if you want to export the individual 
results per realization you must set explicitly ``collect_rlzs=false``.

Note 2: ``collect_rlzs`` is not the inverse of the ``individual_rlzs`` flag. The ``collect_rlzs`` flag indicates to the 
engine that it should pool together the hazard realizations into a single collective bucket that will then be used to 
approximate the branch-averaged risk metrics directly, without going through the process of first computing the 
individual branch results and then getting the weighted average results from the branch results. Whereas the 
``individual_rlzs`` flag indicates to the engine that the user is interested in storing and exporting the hazard (or risk) 
results for every realization. Setting ``individual_rlzs`` to ``false`` means that the engine will store only the 
statistics (mean and quantile results) in the datastore.

Note 3: ``collect_rlzs`` is completely ignored in the hazard part of the calculation, i.e. it does not affect at all 
the computation of the GMFs, only the computation of the risk metrics.


Aggregating by multiple tags
----------------------------

The engine also supports aggregation by multiple tags. Multiple tags can be indicated as multi-tag and/or various 
single-tag aggregations:

``aggregate_by = NAME_1, taxonomy``

or

``aggregate_by = NAME_1; taxonomy``

Comma ``,`` separated values will generate keys for all the possible combinations of the indicated tag values, while 
semicolon ``;`` will generate keys for the single tags.

For instance the second event based risk demo (the file ``job_eb.ini``) has a line

``aggregate_by = NAME_1, taxonomy``

and it is able to aggregate both on geographic region (``NAME_1``) and on ``taxonomy``. There are 25 possible 
combinations, that you can see with the command oq show agg_keys::

	$ oq show agg_keys
	| NAME_1_ | taxonomy_ | NAME_1      | taxonomy                   |
	+---------+-----------+-------------+----------------------------+
	| 1       | 1         | Mid-Western | Wood                       |
	| 1       | 2         | Mid-Western | Adobe                      |
	| 1       | 3         | Mid-Western | Stone-Masonry              |
	| 1       | 4         | Mid-Western | Unreinforced-Brick-Masonry |
	| 1       | 5         | Mid-Western | Concrete                   |
	| 2       | 1         | Far-Western | Wood                       |
	| 2       | 2         | Far-Western | Adobe                      |
	| 2       | 3         | Far-Western | Stone-Masonry              |
	| 2       | 4         | Far-Western | Unreinforced-Brick-Masonry |
	| 2       | 5         | Far-Western | Concrete                   |
	| 3       | 1         | West        | Wood                       |
	| 3       | 2         | West        | Adobe                      |
	| 3       | 3         | West        | Stone-Masonry              |
	| 3       | 4         | West        | Unreinforced-Brick-Masonry |
	| 3       | 5         | West        | Concrete                   |
	| 4       | 1         | East        | Wood                       |
	| 4       | 2         | East        | Adobe                      |
	| 4       | 3         | East        | Stone-Masonry              |
	| 4       | 4         | East        | Unreinforced-Brick-Masonry |
	| 4       | 5         | East        | Concrete                   |
	| 5       | 1         | Central     | Wood                       |
	| 5       | 2         | Central     | Adobe                      |
	| 5       | 3         | Central     | Stone-Masonry              |
	| 5       | 4         | Central     | Unreinforced-Brick-Masonry |
	| 5       | 5         | Central     | Concrete                   |

The lines in this table are associated to the generalized *aggregation ID*, ``agg_id`` which is an index going from ``0`` 
(meaning aggregate assets with NAME_1=*Mid-Western* and taxonomy=*Wood*) to ``24`` (meaning aggregate assets with 
NAME_1=*Central* and taxonomy=*Concrete*); moreover ``agg_id=25`` means full aggregation.

The ``agg_id`` field enters in risk_by_event and in outputs like the aggregate losses; for instance::

	$ oq show agg_losses-rlzs
	| agg_id | rlz | loss_type     | value       |
	+--------+-----+---------------+-------------+
	| 0      | 0   | nonstructural | 2_327_008   |
	| 0      | 0   | structural    | 937_852     |
	+--------+-----+---------------+-------------+
	| ...    + ... + ...           + ...         +
	+--------+-----+---------------+-------------+
	| 25     | 1   | nonstructural | 100_199_448 |
	| 25     | 1   | structural    | 157_885_648 |

The exporter (``oq export agg_losses-rlzs``) converts back the ``agg_id`` to the proper combination of tags; ``agg_id=25``, 
i.e. full aggregation, is replaced with the string ``*total*``.

It is possible to see the ``agg_id`` field with the command ``$ oq show agg_id``.

By knowing the number of events, the number of aggregation keys and the number of loss types, it is possible to give an 
upper limit to the size of ``risk_by_event``. In the demo there are 1703 events, 26 aggregation keys and 2 loss types, 
so ``risk_by_event`` contains at most::

	1703 * 26 * 2 = 88,556 rows

This is an upper limit, since some combination can produce zero losses and are not stored, especially if the 
``minimum_asset_loss`` feature is used. In the case of the demo actually only 20,877 rows are nonzero::

	$ oq show risk_by_event
	       event_id  agg_id  loss_id           loss      variance
	...
	[20877 rows x 5 columns]

It is also possible to perform the aggregation by various single-tag aggregations, using the ``;`` separator instead of 
``,``. For example, a line like::

	aggregate_by = NAME_1; taxonomy

would produce first the aggregation by geographic region (``NAME_1``), then by ``taxonomy``. In this case, instead of 
producing 5 x 5 combinations, only 5 + 5 outputs would be obtained.

ignore_covs vs ignore_master_seed
---------------------------------

The vulnerability functions using continuous distributions (lognormal/beta) to characterize the uncertainty in the loss 
ratio, specify the mean loss ratios and the corresponding coefficients of variation for a set of intensity levels.

There is clearly a performance/memory penalty associated with the propagation of uncertainty in the vulnerability to 
losses. You can completely remove it by setting

``ignore_covs = true``

in the *job.ini* file. Then the engine would compute just the mean loss ratios by ignoring the uncertainty i.e. the 
coefficients of variation. Since engine 3.12 there is a better solution: setting

``ignore_master_seed = true``

in the *job.ini* file. Then the engine will compute the mean loss ratios but also store information about the 
uncertainty of the results in the asset loss table, in the column “variance”, by using the formulae

.. math::

  variance = {\sum}_{i}{\sigma_{i}}^2\ for\ asset\_correl = 0\\
  variance = ({\sum}_{i}{\sigma_{i}})^2\ for\ asset\_correl = 1

in terms of the variance of each asset for the event and intensity level in consideration, extracted from the asset 
loss and the coefficients of variation. People interested in the details should look at the implementation in 
`gem/oq-engine <https://github.com/gem/oq-engine/blob/master/openquake/risklib/scientific.py>`_.
