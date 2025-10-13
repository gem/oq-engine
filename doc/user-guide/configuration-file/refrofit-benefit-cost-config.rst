Retrofit Benefit-Cost Ratio
---------------------------

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