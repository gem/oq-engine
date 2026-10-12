.. _ses-workflows:

Stochastic event sets and calculation workflows
================================================

For large event-based studies it is often useful to separate rupture
sampling from the generation of ground-motion fields (GMFs) and the risk
calculation. The ruptures can be generated once, stored in an HDF5 file, and
then reused for different site collections, exposures, or risk models.

This approach provides a common set of events across the downstream
calculations. It does not make the resulting GMFs identical when the sites
are split differently: the ground motions are sampled for the sites in each
calculation. See :ref:`risk-calculations` for a discussion of this caveat.

Generating a reusable SES datastore
-----------------------------------

An event-based hazard job can sample the stochastic event set without
generating GMFs by setting::

  calculation_mode = event_based
  ground_motion_fields = false

The job must still define its source model, ground-motion logic tree,
investigation time, logic-tree sampling, and SES parameters. Running such a
job creates a normal engine datastore containing the sampled ruptures and
events. Like every engine datastore, it is an HDF5 file, normally named
``calc_<calculation_id>.hdf5``. This is the general approach for both GEM
models and independently developed hazard models; it does not require a
``mosaic_model`` setting or a three-letter model code.

Run the rupture-only job in the usual way::

  oq run job_ses.ini

Keep the calculation ID printed by the engine. A downstream calculation can
refer to that ID, or directly to the corresponding HDF5 datastore.

Building a combined GEM Mosaic SES
----------------------------------

The ``build_ses`` postprocessor can combine ruptures from several GEM Mosaic
models and give the combined SES a chosen filename. This is a specialised
multi-model workflow rather than a requirement for using an SES. For example,
save the following as ``ses.toml``::

  [workflow]
  description = "Build a reusable SES"
  calculation_mode = "event_based"
  ground_motion_fields = false
  number_of_logic_tree_samples = 200
  ses_per_logic_tree_path = 50
  minimum_magnitude = 5

  [EUR]
  ini = "EUR/job_hazard.ini"
  mosaic_model = "EUR"

  [MIE]
  ini = "MIE/job_hazard.ini"
  mosaic_model = "MIE"

  [success]
  func = "openquake.engine.postjobs.build_ses"
  out_file = "ses.hdf5"

Run the workflow with::

  oq run ses.toml

The ``EUR`` and ``MIE`` calculations can run concurrently. If both complete,
the postprocessor merges their site collections, ruptures, events, logic
trees, and calculation parameters into ``ses.hdf5``. The output path is
relative to the TOML file.

In the current implementation, each calculation contributing to this kind
of combined SES must have a unique three-letter ``mosaic_model`` code. Its
TOML job name must end with that code, as in ``EUR`` or ``hazardEUR``. This
is a constraint of the GEM Mosaic merger, not a general requirement on
external hazard models or ordinary engine datastores. Do not invent a Mosaic
code for a single external model; use its rupture-only calculation datastore
directly instead.

The postprocessor retains the ruptures labelled with each selected model.
The modeller remains responsible for checking that the models form a
scientifically appropriate combination. The ``build_ses`` postprocessor is
called only after every unexpected job failure has been resolved. Do not
treat the output file as complete unless the postprocessor has run
successfully.

Starting a GMF calculation from the SES
---------------------------------------

A subsequent ``event_based`` calculation can read the ruptures from the SES
instead of sampling them again. Its configuration file supplies the sites
or site model, intensity measure types, GMF parameters, and any requested
hazard-curve outputs. It does not need source or GSIM logic-tree files,
because the required model information is stored in the SES. A minimal
outline is::

  [general]
  description = GMFs from a reusable SES
  calculation_mode = event_based

  [geometry]
  site_model_file = site_model.csv

  [logic_tree]
  number_of_logic_tree_samples = 200
  ses_per_logic_tree_path = 50
  investigation_time = 1

  [calculation]
  intensity_measure_types_and_levels = {"PGA": logscale(.001, 1, 20)}
  truncation_level = 3
  minimum_intensity = .02
  maximum_distance = 200
  hazard_curves_from_gmfs = true

Pass the calculation ID of a rupture-only job with ``--hc``::

  oq run job_gmf.ini --hc 42

The HDF5 pathname can be used instead::

  oq run job_gmf.ini --hc /path/to/calc_42.hdf5

For a combined Mosaic SES, pass the generated ``ses.hdf5`` file in the same
way.

Alternatively, set ``hazard_calculation_id`` to the HDF5 pathname in the
``job.ini`` file. An absolute path avoids ambiguity. Within a TOML workflow,
relative HDF5 paths are resolved relative to the TOML file.

The rupture-sampling parameters should remain consistent with those used to
create the SES. Parameters controlling the GMFs, including the sites,
intensity measure types, truncation, correlation, and minimum intensity, are
defined by the downstream job.

Starting a risk calculation from the SES
----------------------------------------

An ``event_based_risk`` or ``event_based_damage`` calculation can also use
the SES directly. The risk job defines the exposure, vulnerability or
fragility functions, aggregation settings, and risk outputs. For example::

  [general]
  description = Event-based risk from a reusable SES
  calculation_mode = event_based_risk

  [exposure]
  exposure_file = exposure_model.xml

  [vulnerability]
  structural_vulnerability_file = vulnerability.xml

  [hazard]
  number_of_logic_tree_samples = 200
  ses_per_logic_tree_path = 50
  investigation_time = 1

  [risk_calculation]
  master_seed = 42
  risk_investigation_time = 1
  minimum_intensity = .02
  maximum_distance = 200

Run it with the calculation ID of the rupture-only job::

  oq run job_risk.ini --hc 42

Alternatively, use the path to either a regular engine datastore or a
combined Mosaic SES::

  oq run job_risk.ini --hc /path/to/ses.hdf5

The engine filters the stored ruptures for the risk sites, generates the
required ground motions, and applies the risk functions. Reusing the SES
therefore avoids resampling the ruptures, but it does not reuse previously
generated GMFs.

Managing several calculations with TOML
---------------------------------------

A workflow file groups calculations that belong together. The main pieces
of the format are:

* ``[workflow]`` defines one batch and its shared calculation parameters.
  It must include a ``description``.
* A table such as ``[EUR]`` defines one job. It must contain an ``ini``
  pathname and may override supported shared parameters for that job. Job
  names must start with an uppercase letter and contain at most 20
  characters.
* ``[success]`` defines a postprocessing function called after the jobs
  complete. Use ``[[success]]`` for more than one postprocessor.
* ``[multi.workflow]`` defines shared parameters for a sequence of batches.
  Tables such as ``[hazard.EUR]`` and ``[risk.FRA]`` place jobs in the
  ``hazard`` and ``risk`` batches. Batches run in file order; jobs within a
  batch can run concurrently.

Values in a job's ``job.ini`` file provide the baseline. Supported settings
in ``[workflow]`` or ``[multi.workflow]`` override the INI values, and a
value in an individual job table overrides the workflow default. Common
workflow settings include ``calculation_mode``, ``ground_motion_fields``,
``number_of_logic_tree_samples``, ``ses_per_logic_tree_path``,
``minimum_magnitude``, and ``hazard_calculation_id``. Relative INI and HDF5
paths are resolved from the directory containing the TOML file.

The following Mosaic-specific multi-workflow builds a combined SES before
starting two risk jobs::

  [multi.workflow]
  description = "Build an SES and calculate risk"
  number_of_logic_tree_samples = 200
  ses_per_logic_tree_path = 50

  [hazard.EUR]
  ini = "EUR/job_hazard.ini"
  mosaic_model = "EUR"
  calculation_mode = "event_based"
  ground_motion_fields = false

  [hazard.MIE]
  ini = "MIE/job_hazard.ini"
  mosaic_model = "MIE"
  calculation_mode = "event_based"
  ground_motion_fields = false

  [hazard.success]
  func = "openquake.engine.postjobs.build_ses"
  out_file = "ses.hdf5"

  [risk.FRA]
  ini = "FRA/job_risk.ini"
  hazard_calculation_id = "ses.hdf5"

  [risk.ITA]
  ini = "ITA/job_risk.ini"
  hazard_calculation_id = "ses.hdf5"

Run it in the same way as a single workflow::

  oq run jobs.toml

The engine creates a workflow calculation that records every child
calculation, its status, and the postprocessors that have completed. The
workflow ID is shown in the log and can be used to continue an interrupted
or failed workflow::

  oq run jobs.toml --workflow-id 42

Jobs already marked ``complete`` are skipped, and completed postprocessors
are not repeated. Use the same TOML file when continuing a workflow.

Calculation caching is separate from continuation and is disabled by
default. It can reuse a previous calculation with the same input checksum,
including across separate workflow runs::

  oq run jobs.toml -p cache=true

For large workflows, ``--kfilter`` accepts a regular expression and runs
only matching job names. Run ``oq run --help`` for the complete command-line
interface.

The HDF5 datastore is an engine-native format and can change between engine
versions. Generate and consume an SES with the same OpenQuake engine version
wherever possible, and retain the original inputs needed to reproduce it.
