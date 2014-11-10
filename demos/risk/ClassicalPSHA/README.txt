Classical PSHA-based Risk Demo
==============================

In this example, we first compute hazard curves for the intensity measure types (IMTs) defined in the vulnerability models, for the sites of interest defined in the exposure model. From each curve set we interpolate hazard maps at 10%, 5% and 2% probabilities of exceedance in 50 years.

The hazard curves produced in the above step are then used to compute loss curves for the assets defined in the exposure model. From each curve set we interpolate loss maps at 10%, 5% and 2% probabilities of exceedance in 50 years.

Note: This calculation demo consists of two parts: hazard and risk. The hazard and risk calculations are defined in separate job configuration (.ini) files and were designed to be run together to demonstrate a complete end-to-end demonstration of the workflow for classical PSHA-based risk calculations.

Hazard
------
Expected runtime: 2 minutes
Number of sites: 9144
Number of logic tree realizations: 1
GMPEs: ChiouYoungs2008
IMTs: PGA
Outputs: Hazard Curves, Hazard Maps

Risk
----
Expected runtime: 1 minute
Loss types: Structural, Nonstructural, Occupants
Number of taxonomies: 5
Outputs: Loss Curves, Loss Maps