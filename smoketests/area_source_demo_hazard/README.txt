The demo provides an example of Classical PSHA, using a source model based on
area sources.  The source model is derived from the GSHAP hazard model for
South East Asia.  The source model logic tree contains only the source model,
no additional epistemic uncertainties are considered. The GMPE logic tree
contanins only one GMPE (Boore and Arkinson 2008) associated to Shallow Active
Crust (all the sources are marked as Shallow Active Crust).  The configuration
file (config.gem) is set to compute hazard curves and hazard maps for a small
region (2 by 2 degrees) located in India. Three files are generated: hazard
curves, mean hazard curves - identical to the hazard curves given the absence
of epistemic uncertainties, and mean hazard maps corresponding to 10 and 2%
probability of exceedence in 50 years.
