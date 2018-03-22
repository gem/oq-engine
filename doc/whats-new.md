Release notes for the OpenQuake Engine, version 3.0
===================================================

This release drops support for Python 2.7, now the engine requires Python 3.5+
to run. Several new features entered, in particular in the disaggregation
calculator and in the exposure support.
Over 80 issues were closed. For the complete
list of changes, please see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.0/debian/changelog .

Hazard
--------------

The task distribution has been improved even more, in particular for
event based hazard calculations.

Bug: event_based_rupture calculator generating too few tasks.

We improved the splitting algorithm for the sources, result in faster
calculations.

We made relocatable the export in case of gmpe_table.

We extended the check on duplicated IDs in the source model to models in
the NRML 0.5 format.

`investigation_time` and `start_time` in source models 

Better error message when there are duplicated sites in the CSV

Fix years on event_based_rupture calculator with sampling

Log information about the floating/spinning factors

Event based mutex sources

Hazard disaggregation
---------------------

We fixed a small bug in the disaggregation calculation: we were
reading the source model twice without reason.

We implemented statistical disaggregation outputs.

disagg_outputs is now honored.

Disaggregation by source is in.


Hazardlib/HMTK/SMTK
--------------------

We optimized the Yu et al. (2013) GMPEs for China which is now several time
faster than before.

Graeme Weatherill ported the [Strong Motion Toolkit]
(https://github.com/GEMScienceTools/gmpe-smtk) which depends on hazardlib
and is a part of the OpenQuake suite to Python 3.5.


Risk
-----

The management of the exposure has been refactored and improved. As
a consequence it is not possible to export risk results produced
by previous versions of the engine with engine 3.0. On the plus side
it is now possible to run a risk calculation from a pre-imported
exposure. This is very importance because now the engine is powerful
enough to run calculations with millions of assets and it is convenient
to avoid reimporting them every time if the exposure does not change.

Made it possible to use a pre-imported risk model.

Extended `get_site_collection` to read the sites from the hazard
curves when available

Fixed bug in classical_risk
when `num_statistics > num_realizations`.

Fixed small negative numbers in scenario_damage outputs due to rounding errors.

Aggregating the avg_losses for event_based_risk

Only one realization is accepted in GMFs in CSV format

When running a scenario calculation using precomputed gmfs, the
following error message appears when the IMTs in the gmf are not
compatible with the IMTs in the fragility/vulnerability file

Added a check against duplicated fields in the exposure CSV

WebAPI/WebUI/QGIS plugin
-----------------------------------------------------

We fixed some permission bugs with the WebUI when groups are involved.

Added more risk outputs to the extract API

Bug fixes/additional checks
------------------------------

oq commands
-----------

The command `oq info` has been extended to source model logic tree files:
in that case it reports a summary for the full composite source model.

The command `oq dbserver stop` and `oq workers stop` now correctly
stops the zmq workers (relevant for the experimental zmq mode).

IT
---

A huge improvement has been made in cluster situations: now the results
are returned via [ZeroMQ](http://zeromq.org/) and not via rabbimq.
This allows to bypass the limit of rabbitmq and larger computations can 
be run without running out of disk space in the mnesia directory.
Hundreds of thousands of tasks can be generated without issue, a feat
previously impossible.

Task distribution code has been simplified:
code in the state experimental/proof-of-concept has been removed: in
particular the support to ipython and the support to SGE. As it is
now, they are not used and still a significant maintenance cost.

Made it possible to import remote calculations

Use port 1907 for the DbServer in packages

Deprecations/removals
---------------------

The old commands `oq engine --run-hazard` and `oq engine --run-risk`, deprecated
two years ago, have been finally removed. The only command to use to run
calculations is `oq engine --run`, without distinction between hazard and
risk.
