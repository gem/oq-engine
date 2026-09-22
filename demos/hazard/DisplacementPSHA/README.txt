Probabilistic Fault Displacement (PFD) hazard map
==================================================

This demo computes the annual rate of earthquake-induced surface fault
displacement exceeding a set of displacement levels over a region around two
fault traces, in the OpenQuake ``displacement`` calculation mode.  Since
``return_periods`` and ``hazard_maps`` are set, it also produces hazard maps
(the displacement exceeded at the given return period).

Inputs
------
job.ini
    region: a 10 km grid over 15.9-16.3 E, 39.2-39.8 N
    intensity_measure_types_and_levels: the "Disp" IMT (metres)
    r_threshold_km: half-width of the on-trace principal zone
    use_rates/disagg_by_src are forced to true by the mode
source_model.xml
    two characteristic fault sources (West_crati, Alt-Mot)
source_model_logic_tree.xml
    a trivial one-branch source-model logic tree
pfd_logic_tree.xml
    the PFD model logic tree, selecting the surface-rupture and
    displacement models for the principal and distributed components

Run it with:

    oq engine --run job.ini

The main outputs are the hazard maps (`hazard_map-mean-...csv`) and the
mean hazard curves (`hazard_curve-mean-Disp.csv`).  `mean_rates_by_src.csv`
gives the per-source contribution, since `disagg_by_src` is enabled.
