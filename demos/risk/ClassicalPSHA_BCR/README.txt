Classical PSHA-based Benefit Cost Ratio Demo
============================================

In this example, we first compute hazard curves for the intensity measure types (IMTs) defined in the vulnerability models, for the sites of interest defined in the exposure model.

The hazard curves produced in the above step are then used to compute retrofit benefit-cost ratios for the assets defined in the exposure model.

Note: This calculation demo consists of two parts: hazard and risk. The hazard and risk calculations are defined in separate job configuration (.ini) files and were designed to be run together to demonstrate a complete end-to-end demonstration of the workflow for classical PSHA-based risk calculations.

Hazard
------
Expected runtime: 2 minutes
Number of sites: 9144
Number of logic tree realizations: 1
GMPEs: ChiouYoungs2008
IMTs: PGA
Outputs: Hazard Curves

Risk
----
Expected runtime: 1 minute
Number of taxonomies: 5
Outputs: Benefit Cost Ratio Maps