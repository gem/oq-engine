Classical Probabilistic Damage Demo
-----------------------------------

In this example, we first compute hazard curves for PGA at different intensity levels, 
for the sites of interest defined by a region grid spacing and the exterior polygon defined
by the assets in the exposure model.

The hazard curves produced in the above step are then used to compute expected damage 
distributions for the assets defined in the exposure model.

Note: This calculation demo consists of two parts: hazard and risk. The hazard and risk 
calculations are defined in separate job configuration (.ini) files and were designed to be 
run together to demonstrate a complete end-to-end demonstration of the workflow for classical 
PSHA-based damage calculations.

**Hazard**  
Expected runtime: 2 minutes  
Number of sites: 2253  
Number of logic tree realizations: 2  
GMPEs: ChiouYoungs2008, AbrahamsonEtAl2014
IMTs: PGA  
Outputs: Hazard Curves, Seismic Source Groups, Realizations

**Risk**  
Expected runtime: 30 seconds 
Number of taxonomies: 5  
Outputs: Asset Damage Distribution, Asset Damage Statistics, Seismic Source Groups, Realizations