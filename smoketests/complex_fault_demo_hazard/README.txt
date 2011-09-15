The demo provides an example of Classical PSHA, using a source model based on
complex fault sources.  The source model is derived from the USGS-NSHMP hazard
model for the Cascadia region.  The source model logic tree contains only the
source model, no additional epistemic uncertainties are considered. The GMPE
logic tree contanins only one GMPE (Boore and Arkinson 2008) associated to
Subduction Interface (all the sources are marked as Subduction Interface).  The
configuration file (config.gem) is set to compute hazard curves and hazard maps
for a small region (2 by 2 degrees) around Seattle. Three files are generated:
hazard curves, mean hazard curves - identical to the hazard curves given the
absence of epistemic uncertainties, and mean hazard maps corresponding to 10
and 2% probability of exceedence in 50 years.
