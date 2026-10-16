.. _ses-workflows:

Stochastic event sets and calculation workflows
================================================

For large event-based studies it is often useful to separate rupture
sampling from the generation of ground-motion fields (GMFs) and the risk
calculation. The ruptures can be generated once, stored in an HDF5 file, and
then reused with different site collections, exposures, or risk models.

This approach provides a common set of events across the downstream
calculations. Note that the resulting GMFs may not be identical when the sites
are split differently, as the ground motions are sampled for the sites in each
calculation. See :ref:`risk-calculations` for a discussion of this caveat.

Generating a reusable SES datastore
-----------------------------------

An event-based hazard job can sample the stochastic event set without
generating GMFs by setting::

  calculation_mode = event_based
  ground_motion_fields = false

The job must still define its source model, ground-motion logic tree,
investigation time, logic-tree sampling, and SES parameters. Running it
creates a normal engine datastore containing the sampled ruptures, events,
logic trees, calculation parameters, and site collection. Like every engine
datastore, it is an HDF5 file, normally named
``calc_<calculation_id>.hdf5``. No special model identifier is required.

Run the rupture-only job in the usual way::

  oq run job_ses.ini

Keep the calculation ID printed by the engine. A downstream calculation can
refer to that ID, or directly to the corresponding HDF5 datastore. The file
can also be copied to a more descriptive name, such as ``SES.hdf5``.

Choosing the output filename in a TOML workflow
-----------------------------------------------

When several rupture-only calculations are combined, for instance while
building a single SES from multiple hazard models, the ``build_ses``
postprocessor can write the resulting datastore to a chosen location. Set
the filename or path with ``out_file`` in the ``[success]`` table::

  [workflow]
  description = "Build a reusable SES"
  calculation_mode = "event_based"
  ground_motion_fields = false
  number_of_logic_tree_samples = 200
  ses_per_logic_tree_path = 50

  [HazardAAA]
  ini = "model_a/job_hazard.ini"
  mosaic_model = "AAA"

  [HazardBBB]
  ini = "model_b/job_hazard.ini"
  mosaic_model = "BBB"

  [success]
  func = "openquake.engine.postjobs.build_ses"
  out_file = "SES.hdf5"

Run the workflow with::

  oq run ses.toml

The two rupture-only calculations can run concurrently. After they complete
successfully, the postprocessor writes ``SES.hdf5``. A relative
``out_file`` path is resolved from the directory containing the TOML file;
an absolute path can be used instead. The output directory must already
exist.

The remaining requirements in this section apply only when several
rupture-only calculations are merged. They are not needed when an ordinary
single-calculation datastore is reused directly.

Despite its name, ``mosaic_model`` is a generic identifier for a hazard
model in a multi-model calculation; it is not restricted to GEM models.
Users can supply their own three-letter model identifiers, using uppercase
ASCII letters, and their own model boundaries. Each polygon in the boundary
GeoPackage must have a ``name`` attribute containing the corresponding
identifier.

The boundary file can be set explicitly in the ``[directory]`` section of
``openquake.cfg``::

  [directory]
  mosaic_boundaries_file = /absolute/path/to/mosaic.gpkg

If that setting is empty, the engine looks for ``mosaic.gpkg`` in the
configured ``mosaic_dir``. If that file does not exist, it uses the copy
bundled with the engine at
``openquake/qa_tests_data/mosaic/mosaic.gpkg``. An explicitly configured
``mosaic_boundaries_file`` is used as given; an invalid path raises an error
instead of falling back. The engine logs the path that it reads. Custom
model codes are accepted, although the reader may warn that they are not in
the bundled model list.

For each calculation passed to ``build_ses``, the model identifier connects
three pieces of information: the model assigned to each rupture using the
boundary polygons, the logic tree stored under ``full_lt/<model>`` in the
combined datastore, and the calculation parameters stored under the TOML
job name.

The current implementation stores this identifier in a three-byte field and
recovers it from the last three characters of the TOML job name.
For example, a job named ``HazardABC`` must set
``mosaic_model = "ABC"``, and the boundary file must contain a polygon whose
``name`` is ``ABC``. If these values do not agree, ruptures may be omitted
during the merge or a downstream calculation may be unable to find the
corresponding logic tree and calculation parameters.

The three-letter convention is a constraint of the current multi-model
merger, not of the SES HDF5 format.

What is reused from the SES
---------------------------

The SES supplies the sampled ruptures and events, their realization
mapping, the source-model and GSIM logic trees, the parameters stored with
the original calculation, and its site collection. The stored site
collection can provide site parameters for nearby sites in a downstream
calculation.

The downstream job supplies the sites or exposure to be analysed, the IMTs,
the GMF and risk settings, and the requested outputs. Values explicitly set
by the downstream job take precedence where the parameter can be
overridden. The sampling metadata parameters ``investigation_time``,
``number_of_logic_tree_samples``, and ``ses_per_logic_tree_path`` must remain
consistent with the SES because they describe its effective time and
realization structure. Specifying those values does not resample ruptures.

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
  # These values must match the SES.
  number_of_logic_tree_samples = 200
  ses_per_logic_tree_path = 50
  investigation_time = 1

  [calculation]
  intensity_measure_types_and_levels = {"PGA": logscale(.001, 1, 20)}
  truncation_level = 3
  minimum_intensity = .02
  maximum_distance = 200
  hazard_curves_from_gmfs = true

Pass the calculation ID of the rupture-only job with ``--hc``::

  oq run job_gmf.ini --hc 42

The HDF5 pathname can be used instead::

  oq run job_gmf.ini --hc /path/to/SES.hdf5

Alternatively, set ``hazard_calculation_id`` to the HDF5 pathname in the
``job.ini`` file. An absolute path avoids ambiguity. Within a TOML workflow,
relative HDF5 paths are resolved relative to the TOML file.

The sites, intensity measure types, truncation, correlation, minimum
intensity, and hazard-curve outputs in this example are settings for the new
GMF calculation. The ruptures and their logic-tree associations come from
the SES.

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
  # These values must match the SES.
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

Alternatively, use the path to the datastore::

  oq run job_risk.ini --hc /path/to/SES.hdf5

The engine filters the stored ruptures for the risk sites, generates the
required ground motions, and applies the risk functions. Reusing the SES
therefore avoids resampling the ruptures, but it does not reuse previously
generated GMFs. The exposure, vulnerability or fragility functions,
aggregation settings, risk seed, and risk outputs belong to the downstream
risk calculation.

Inspecting an SES datastore
---------------------------

The main datasets used by a downstream calculation are ``ruptures``,
``rupgeoms``, ``events``, ``full_lt``, ``oqparam``, and ``sitecol``. Users
normally do not need to inspect these datasets directly.

In a regular calculation datastore, ``full_lt`` contains one full logic
tree. In a combined SES it is a group containing one logic tree per model,
under ``full_lt/<model>``. The ``oqparam`` dataset follows the same pattern:
it is a single object in a regular datastore and a group keyed by TOML job
name in a combined SES.

The ``trt_smr`` rupture field identifies the tectonic region type and source
model realization. The engine supports at most 256 tectonic region types,
which fit in one byte, and ``2**24`` source model realizations, which fit in
three bytes. It combines both indices in one 32-bit value. Extract them as
follows::

  trt, smr = divmod(trt_smr, 2**24)

After selecting the appropriate ``full_lt`` object, use the indices to
obtain the tectonic region type and source model realization::

  full_lt.trts[trt]
  full_lt.sm_rlzs[smr]

Show the source model realizations for a regular datastore with::

  oq show sm_rlzs SES.hdf5

For a combined SES, append the model identifier to the view name::

  oq show sm_rlzs:ABC SES.hdf5

The following script counts ruptures by model and tectonic region type. It
works with both regular and combined SES datastores:

.. code-block:: python

 from openquake.baselib import sap, hdf5
 TWO24 = 2 ** 24

 def main(ses_hdf5):
     """Count the ruptures by model and TRT."""
     with hdf5.File(ses_hdf5) as f:
         ruptures = f['ruptures'][:]
         full_lt = f['full_lt']
         if hasattr(full_lt, 'trts'):
             full_lts = [('???', full_lt)]
         else:
             full_lts = [(model, f[f'full_lt/{model}'])
                         for model in full_lt]
         for model, full_lt in full_lts:
             rups = ruptures if model == '???' else ruptures[
                 ruptures['model'] == model.encode('ascii')]
             trt_indices = rups['trt_smr'] // TWO24
             for i, trt in enumerate(full_lt.trts):
                 print(model, trt, (trt_indices == i).sum())

 if __name__ == '__main__':
     sap.run(main)

Managing several calculations with TOML
---------------------------------------

A TOML workflow groups calculations that belong together and avoids running
each ``job.ini`` separately. For example, the following workflow runs two
risk calculations using the same SES::

  [workflow]
  description = "Risk calculations using a common SES"
  hazard_calculation_id = "SES.hdf5"
  number_of_logic_tree_samples = 200
  ses_per_logic_tree_path = 50

  [Residential]
  ini = "residential/job_risk.ini"

  [Commercial]
  ini = "commercial/job_risk.ini"

Save the file as ``jobs.toml`` and run::

  oq run jobs.toml

The two jobs can run concurrently. Their ``job.ini`` files provide the
baseline configuration. A supported setting in ``[workflow]`` overrides the
same setting in every INI file, while a setting in an individual job table
overrides the workflow default. For example::

  [Residential]
  ini = "residential/job_risk.ini"
  minimum_magnitude = 5.5

Common workflow settings include ``calculation_mode``,
``ground_motion_fields``, ``number_of_logic_tree_samples``,
``ses_per_logic_tree_path``, ``minimum_magnitude``, and
``hazard_calculation_id``. Relative INI and HDF5 paths are resolved from the
directory containing the TOML file.

The main parts of the format are:

* ``[workflow]`` defines one batch and its shared calculation parameters.
  It must include a ``description``.
* A table such as ``[Residential]`` defines one job. It must contain an
  ``ini`` pathname and may override supported shared parameters. Job names
  must start with an uppercase letter and contain at most 20 characters.
* ``[success]`` defines an optional postprocessing function called after all
  jobs complete successfully. Use ``[[success]]`` for more than one
  postprocessor.

For calculations that must be divided into ordered batches, use
``[multi.workflow]``. Tables with the same prefix form a batch; batches run
in file order, while jobs within one batch can run concurrently::

  [multi.workflow]
  description = "Ordered calculation batches"

  [baseline.Reference]
  ini = "baseline/job.ini"

  [sensitivity.Low]
  ini = "sensitivity/low/job.ini"

  [sensitivity.High]
  ini = "sensitivity/high/job.ini"

Here ``baseline`` runs first. If it succeeds, the two ``sensitivity`` jobs
run as the second batch. A multi-workflow does not automatically substitute
the calculation IDs from one batch into the next; dependent jobs must refer
to their inputs explicitly.

Continuing and filtering a workflow
-----------------------------------

The engine creates a workflow calculation that records every child
calculation, its status, and any postprocessors that have completed. The
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
