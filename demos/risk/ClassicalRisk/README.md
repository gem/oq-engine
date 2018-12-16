Classical Probabilistic Risk Demo
---------------------------------

In this example, we first compute hazard curves for the intensity measure types (IMTs)
defined in the vulnerability models, for the sites of interest defined in the exposure model.
From each curve set we interpolate hazard maps at 10% and 2% probabilities of exceedance
in 50 years.

Note: This calculation demo consists of two parts: hazard and risk. The hazard and risk 
calculations are defined in separate job configuration (.ini) files and were designed to be 
run together to demonstrate a complete end-to-end demonstration of the workflow.

**Hazard**  
Expected runtime: 1 minute
Number of sites: 2253  
Number of logic tree realizations: 1  
GMPEs: ChiouYoungs2008, 
IMTs: PGA, SA(0.3)
Outputs: Hazard Curves, Hazard Maps, Seismic Source Groups

**Risk**  
Expected runtime: 10 seconds
Number of taxonomies: 5 
Outputs: Asset Loss Curves Statistics, Asset Loss Maps Statistics, Average Asset Losses Statistics, Seismic Source Groups


