
Classical Damage and Risk
-------------------------

.. _classical-damage-params:

Classical Damage
================

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
earlier in Section :ref:`Scenario Damage Calculator <scenario-damage-params>`. The parameters related to the hazard curves computation have been 
described earlier in Section :ref:`Classical PSHA <classical-psha-params>`.

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
sequentially or separately, as illustrated in Example 2 in Section :ref:`Scenario Damage Calculator <scenario-damage-params>`. 
The new parameters introduced in the above example configuration file are described below:

- ``risk_investigation_time``: an optional parameter that can be used in probabilistic damage or risk calculations where the period of interest for the risk calculation is different from the period of interest for the hazard calculation. If this parameter is not explicitly set, the OpenQuake engine will assume that the risk calculation is over the same time period as the preceding hazard calculation.
- ``steps_per_interval``: an optional parameter that can be used to specify whether discrete fragility functions in the fragility models should be discretized further, and if so, how many intermediate steps to use for the discretization. Setting ``steps_per_interval = n`` will result in the OpenQuake engine discretizing the discrete fragility models using (n - 1) linear interpolation steps between each pair of intensity level, poe points. The default value of this parameter is one, implying no interpolation.

.. _classical-risk-params:

Classical Risk
==============

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
Section :ref:`Classical Probabilistic Seismic Damage Calculator <classical-damage-params>` is the use of a 
vulnerability model instead of a fragility model.

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
sequentially or separately, as illustrated in Example 2 in Section :ref:`Scenario Damage Calculator <scenario-damage-params>`. 
The new parameters introduced in the above risk configuration file example are described below:

- ``lrem_steps_per_interval``: this parameter controls the number of intermediate values between consecutive loss ratios (as defined in the Vulnerability Model) that are considered in the risk calculations. A larger number of loss ratios than those defined in each Vulnerability Function should be considered, in order to better account for the uncertainty in the loss ratio distribution. If this parameter is not defined in the configuration file, the OpenQuake engine assumes the ``lrem_steps_per_interval`` to be equal to 5. More details are provided in the OpenQuake Book (Risk).
- ``quantiles``: this parameter can be used to request the computation of quantile loss curves for computations involving non-trivial logic trees. The quantiles for which the loss curves should be computed must be provided as a comma separated list. If this parameter is not included in the configuration file, quantile loss curves will not be computed.
- ``conditional_loss_poes``: this parameter can be used to request the computation of probabilistic loss maps, which give the loss levels exceeded at the specified probabilities of exceedance over the time period specified by ``risk_investigation_time``. The probabilities of exceedance for which the loss maps should be computed must be provided as a comma separated list. If this parameter is not included in the configuration file, probabilistic loss maps will not be computed.
