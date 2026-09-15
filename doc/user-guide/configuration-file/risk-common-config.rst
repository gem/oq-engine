.. _risk-common-params:

Common risk parameters
----------------------

This section summarises the structure of the information necessary to define the different input data to be used with 
the OpenQuake engine risk calculators. Input data for scenario-based and probabilistic seismic damage and risk analysis 
using the OpenQuake engine are organised into:

- An exposure model file in the NRML format, as described in Section :ref:`Exposure Models <exposure-models>`.
- A file describing the *Vulnerability Model* (Section :ref:`Vulnerability Models <vulnerability-models>`) for loss calculations, or a file describing the *Fragility Model* (Section :ref:`Fragility Models <fragility-models>`) for damage calculations. Optionally, a file describing the *Consequence Model* (Section :ref:`Consequence Models <consequence-models>`) can also be provided in order to calculate losses from the estimated damage distributions.
- A general calculation configuration file.
- Hazard inputs. These include hazard curves for classical damage and risk,
  ground motion fields for scenario damage and risk, or stochastic event sets
  for event-based calculations. The hazard can be provided in three ways:

  - Compute hazard and risk sequentially from a single configuration file.
    This is the preferred approach when both input models are available.
  - Run the risk configuration against a compatible hazard calculation in
    the engine datastore, using ``--hazard-calculation-id`` (or ``--hc``).
    The hazard and risk configurations can therefore be run separately.
  - Supply exported hazard results as CSV files. Use
    ``hazard_curves_csv`` for classical damage or risk and ``gmfs_csv`` for
    scenario damage or risk. The relevant calculator sections describe the
    required files and metadata.

The file formats for *Exposure models*, *Fragility Models*, *Consequence Models*, and *Vulnerability models* have been 
described earlier in :ref:`Risk Input Models <input-models>`. The configuration file is the primary file that provides the OpenQuake 
engine information regarding both the definition of the input models (e.g. exposure, site parameters, fragility, 
consequence, or vulnerability models) as well as the parameters governing the risk calculation.

Some initial mandatory parameters of the configuration file common to all of the risk calculators are presented in the listing. 
The remaining parameters that are specific to each risk calculator are discussed in subsequent sections::

	[general]
	description = Example risk calculation
	calculation_mode = scenario_risk
	
	[exposure]
	exposure_file = exposure_model.xml
	

- ``description``: a parameter that can be used to include some information about the type of calculations that are going to be performed.
- ``calculation_mode``: this parameter specifies the type of calculation to
  be run. Valid risk options include ``scenario_damage``, ``scenario_risk``,
  ``classical_damage``, ``classical_risk``, ``event_based_damage``,
  ``event_based_risk``, and ``classical_bcr``.
- ``exposure_file``: this parameter is used to specify the path to the Exposure Model file. Typically this is the path to the xml file containing the exposure, or the xml file containing the metadata sections for the case where the assets are listed in one or more csv files. For particularly large exposure models, it may be more convenient to provide the path to a single compressed zip file that contains the exposure xml file and the exposure csv files (if any).

Depending on the type of risk calculation, other parameters besides the aforementioned ones may need to be provided. We 
illustrate in the following sections different examples of the configuration file for the different damage and risk calculators.
