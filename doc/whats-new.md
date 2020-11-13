This is a major release featuring several optimizations, new features,
and a bug fixes. Over 300 pull requests were merged.

For the complete list of changes, see the changelog:
https://github.com/gem/oq-engine/blob/engine-3.11/debian/changelog

Here are the highlights.

# New features

It is now possible to perform a sensitivity analysis, i.e. to run multiple
calculations with different values of one ore more parameters with a single
command.

Source IDs are now unique internally.

It is possibile to set `num_cores` in openquake.cfg.

# Optimizations

We optimized the GMF saving and export by using pandas.
We worked at the UCERF calculator.
Optimized get_poes and the storage of _poes.
We optimized spectacularly the performance of calculations with particularly
complex logic trees, like the South Africa (ZAF) model.
There is a logic tree path shortener.
We now store the ruptures in a single pandas-friendly dataset, including
information about the generating source.
Changed the source seed algorithm.

# Risk calculators

There was a huge speedup in ebrisk calculation due to the removal of
zero losses.
There was a lot of work on secondary perils.
Added portfolio_damage_error view.

# Other new features/improvements

# hazardlib/HTMK

We introduced a new MFD parameter slipRate.
Implemented AvgPoeGMPE.

# Bugs

# New checks and warnings

# oq commands

Added command `oq compare rups calc1 calc2`.

# WebUI/WebAPI/QGIS plugin

Improved submitting calculations to the WebAPI: now they can be run on a zmq
cluster, `serialize_jobs` is honored and the log level is configurable in
openquake.cfg.
￼
# Packaging

We upgraded h5py to version 2.10.
