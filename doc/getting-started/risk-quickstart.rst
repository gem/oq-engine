.. _risk-quickstart:

Risk quickstart: run a scenario
===============================

This guide takes you through one complete risk calculation. It starts from a
prepared demonstration model so that you can first learn the workflow, then
explore how its inputs are structured.

Before starting, verify that the engine command is available:

.. code-block:: console

   oq --version

If this command fails, follow the :doc:`installation instructions
<installation-instructions/index>` before continuing.

1. Get the demonstration files
------------------------------

Download and extract the
`current demo archive
<https://artifacts.openquake.org/travis/demos-master.zip>`_. The extracted
``demos`` directory contains small hazard and risk examples maintained with
the engine source code.

Open a terminal in the extracted directory and move to the scenario risk
example:

.. code-block:: console

   cd demos/risk/ScenarioRisk

The directory contains:

- ``job.ini``, which selects the calculator and its settings;
- ``fault_rupture.xml``, which describes the earthquake scenario;
- ``exposure_model.xml`` and ``exposure_model.csv``, which describe the
  assets and their values; and
- three vulnerability models, which relate shaking to structural,
  nonstructural, and occupant losses.

These inputs are deliberately simplified and must not be treated as a model
of the actual risk in Nepal.

2. Run the calculation
----------------------

Run the job from the directory containing ``job.ini``:

.. code-block:: console

   oq engine --run job.ini

The job uses ``calculation_mode = scenario_risk``. The engine generates 100
ground-motion fields for the rupture, applies the vulnerability functions to
the exposed assets, and calculates losses. A successful run ends with a
calculation ID and a list of available outputs.

Warnings deserve review, but they do not necessarily mean that the
calculation failed. An error or a final ``failed`` status does.

3. Inspect and export the results
---------------------------------

List every output from the latest calculation:

.. code-block:: console

   oq engine --list-outputs -1

``-1`` means the most recent calculation. It is convenient while learning;
use the displayed positive calculation ID when several calculations are being
compared or automated.

Create an empty output directory and export the latest calculation:

.. code-block:: console

   mkdir results
   oq engine --export-outputs -1 results

The most useful files for a first review are:

- ``avg_losses-rlz-*.csv``: mean loss for each asset and loss type;
- ``aggrisk-*.csv``: loss aggregated over the portfolio;
- ``risk_by_event-*.csv``: aggregate loss for each simulated event;
- ``gmf-data_*.csv``: the ground motions used by the risk calculation; and
- ``report_*.rst``: a summary of the calculation, inputs, and performance.

Output filenames include the calculation ID and can vary slightly between
engine versions. Use ``--list-outputs`` rather than relying on a fixed list of
names or IDs.

4. Check that the results make sense
-------------------------------------

Before interpreting losses, confirm that:

- the log reports that assets were associated with hazard sites;
- the output loss types match the vulnerability files in ``job.ini``;
- monetary losses use the same currency and unit convention as the exposure
  values; and
- occupant losses are counts associated with ``time_event = night``, not
  monetary values.

These checks establish that the files are connected correctly. Scientific
validation of the rupture, ground-motion model, exposure, and vulnerability
functions is a separate and essential step for a real study.

Where to go next
----------------

- Use :ref:`workflows` to choose a calculator for a different question.
- Read :ref:`input-models` before preparing your own exposure and risk
  functions.
- Use the :ref:`risk-common-params` and calculator-specific configuration
  sections when building ``job.ini``.
- Consult the :doc:`output reference </user-guide/outputs/index>` when
  interpreting and post-processing
  results.
- Explore the remaining :doc:`demos and tutorials <demos-tutorials/index>`
  after completing this end-to-end example.
