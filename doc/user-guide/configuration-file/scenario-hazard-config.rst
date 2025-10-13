.. _scenario-hazard-params:

Scenario Hazard
---------------

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
(Section :ref:`Classical PSHA <classical-psha-params>`) and the event-based PSHA calculator (Section :ref:`Event based PSHA <event-based-psha-params>`). The set of sites at which the 
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

************
station_data
************

In a section conventionally called ``[station_data]``, the user specifies the CSV file 
containing the observations::

	[station_data]
	station_data_file = stationlist.csv

This CSV file contains the observed intensity values available from ground motion recordings 
and macroseismic intensity data. One or multiple intensity measure types can be indicated for all observations. An 
example of such a file is shown below in :ref:`the table below <example-station-data-csv>`.

When conditiong the ground motion fields to station data, all of the site parameters required by the GMMs will also need 
to be provided for the set of sites in the station_data_file. This is specified in the configuration file by including 
in the ``site_model_file`` section a ``site_model_stations.csv`` file.

.. _example-station-data-csv:
.. table:: Example of station data CSV file

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


********************
Ground motion models
********************

The user can choose to specify one or multiple GSIMs (or GMPEs) for the scenario calculation using any of the options below. 
A list of available GSIMs can be obtained using ``oq info gsims`` in the terminal, and these are also documented at 
http://docs.openquake.org/oq-engine/stable/openquake.hazardlib.gsim.html.

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
