Scenario Damage and Risk
------------------------

.. _scenario-damage-params:

Scenario Damage
===============

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
	gmfs_file = gmfs.csv
	
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

- ``gmfs_csv``: a parameter used to define the path to the Ground Motion Fields file in the csv format. This file must define Ground Motion Fields for all of the intensity measure types used in the Fragility Model. (`Download an example file here <https://github.com/gem/oq-engine/raw/master/doc/manual/input_scenario_gmfs.csv>`__).
- ``sites_csv``: a parameter used to define the path to the sites file in the csv format. This file must define site id, longitude, and latitude for all of the sites for the Ground Motion Fields file provided using the gmfs_csv parameter. (`Download an example file here <https://github.com/gem/oq-engine/raw/master/doc/manual/input_scenario_sites.csv>`_).

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
	consequence_file = {'taxonomy': "consequence_model.csv"}

Note that the "consequence_model.csv" file will have a structure like the
following::

  taxonomy,consequence,loss_type,ds1,ds2,ds3,ds4
  tax1,losses,contents,1.000000E-01,3.000000E-01,6.000000E-01,9.000000E-01
  tax2,losses,contents,1.000000E-01,3.000000E-01,6.000000E-01,9.000000E-01
  tax3,losses,contents,1.000000E-01,3.000000E-01,6.000000E-01,9.000000E-01
  tax1,losses,nonstructural,5.000000E-02,2.500000E-01,5.000000E-01,7.500000E-01
  tax2,losses,nonstructural,5.000000E-02,2.500000E-01,5.000000E-01,7.500000E-01
  tax3,losses,nonstructural,5.000000E-02,2.500000E-01,5.000000E-01,7.500000E-01
  tax1,losses,structural,4.000000E-02,1.600000E-01,3.200000E-01,6.400000E-01
  tax2,losses,structural,4.000000E-02,1.600000E-01,3.200000E-01,6.400000E-01
  tax3,losses,structural,4.000000E-02,1.600000E-01,3.200000E-01,6.400000E-01

The above calculation can be run using the command line::

	user@ubuntu:~$ oq engine --run job.ini

After the calculation is completed, a message similar to the following will be displayed::

	Calculation 1579 completed in 37 seconds. Results:
	  id | name
	8990 | Average Asset Losses
	8993 | Average Asset Damages

.. _scenario-risk-params:

Scenario Risk
=============

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
