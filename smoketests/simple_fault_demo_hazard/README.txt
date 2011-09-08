The demo provides an example of Classical PSHA, using a source model based on simple fault sources.
The source model is derived from the Database of Individual Seismogenic Sources DISS (http://diss.rm.ingv.it/diss/).
The source model logic tree contains only the source model,
no additional epistemic uncertainties are considered. The GMPE logic tree contanins only one GMPE
(Boore and Arkinson 2008) associated to Shallow Active Crust (all the sources are marked as Shallow Active Crust).
The configuration file (config.gem) is set to compute hazard curves and hazard maps for a small region 
in north west Italy. Three files are generated: hazard curves, mean hazard curves -
identical to the hazard curves given the absence of epistemic uncertainties,
and mean hazard maps corresponding to 10 and 2% probability of exceedence in 50 years.
