What's new in engine-1.3
========================

Here are the novelties of the new release of the OpenQuake Engine, as compared to the latest stable release, 1.2.

0. This is the first engine release to be Ubuntu 14.04 ready. That means that even if we do not provide
Ubuntu 14.04 packages (yet), the engine works with Ubuntu 14.04 and actually we developers
have already switched to that version. Ubuntu 14.10 works too, as well as recent versions of Fedora
and probably other flavors of Linux. Ubuntu 12.04 is still the officially supported version and we will keep to support it for the foreseeable future. The only change which is needed for Ubuntu 12.04 users is to upgrade Django to the release 1.6.1, which is done automatically if you install from the debian packages.

0. The event based risk calculator is able to disaggregate the event loss table per asset.
To enable this feature, just list the assets you are interested in in the job.ini file

  `specific_assets = a1 a2 a3`

1. We have a new hazard calculator, which can be invoked by setting in the job.ini file

  `calculation_mode = classical_tiling`

  This calculators is the same as the classical calculator (i.e. you will get the same numbers) but
  instead of considering all the hazard sites at once, it splits them in tiles and compute the
  hazard curves for each tile sequentially. The intended usage is for very large calculations
  that exceed the available memory. It is especially convenient when you have very large logic trees
  and you are interested only in the statistics (i.e. mean curves and quantile curves). In that case
  you should use it with the option `individual_curves=false`. Notice that this calculator is still in
  an experimental stage and at the moment is does not support UHS curves. Hazard maps and hazard curves
  are supported.

2. We have a new risk calculator, which can be invoked by setting in the job.ini file

  `calculation_mode = classical_damage`

  This calculator is able to compute the damage distribution for each asset starting from the hazard
  curves produced by the classical (or classical_tiling) calculator and a set of fragility functions.
  Also this calculator should be considered in experimental stage.

3. A significant change has been made when the parameter `number_of_logic_tree_samples` is set to a
non-zero value. Now, if a branch of the source model logic tree is sampled twice we will generate the ruptures twice; before the ruptures were generated once and counted twice. For the classical calculator there is no effect on the numbers (sampling the same branch twice will produce two copies of identical ruptures); however, for the event based calculator, sampling the same branch twice will produce different ruptures. For instance, in the case of a simple source model with a single tectonic region type, before we would have generated a single file with the stochastic event sets, now we generate `number_of_logic_tree_samples`  files with different stochastic event sets. The previous behavior was an optimization-induced bug.

4. Several small things were added:

  - better validation of the input files (fragility models, job.ini)
  - the ability to extract the sites from the site_model.xml file
  - several missing QA tests have been added
  - the export mechanism has been enhanced and more outputs are being exported in CSV format
  - there is a new parameter `complex_fault_mesh_spacing`
  - some error messages have been improved

4. A lot of functionality has been ported from the engine to oq-lite, i.e. a lite version of the engine
that does not depend on PostgreSQL/PostGIS/Django nor from RabbitMQ/Celery. This version is much easier to install than the regular engine and it is meant for small/medium computation that do not require a cluster. The engine demos, have been moved to the oq-risklib repository, so that they can be run via the oq-lite command without installing the full engine.

Currently the following calculators have been ported (all are to be intended as experimental):

- classical hazard
- classical tiling
- event based hazard
- scenario hazard
- classical risk
- scenario damage
- classical damage

Others will be ported in the near future.