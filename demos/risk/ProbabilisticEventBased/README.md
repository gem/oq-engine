Probabilistic Event-based Risk Demo
===================================

In this example, we start with a seismic source model for the region of interest, and produce a collection of stochastic event sets (SES). Each SES comprises a set of earthquake rupture realizations for a period of 50 years; 100 such sets are produced. For each rupture in the SES collection, we then compute a ground motion field for the locations of interest defined in the exposure model.

The ground motion fields produced in the above step are then used to compute loss realizations for the assets defined in the exposure model. Statistical analysis of the loss realizations allows us to extract loss curves for the assets, aggregate loss curves, event loss tables, and loss maps at 10%, 5% and 2% probabilities of exceedance in 50 years.

Note: This calculation demo consists of two parts: hazard and risk. The hazard and risk calculations are defined in separate job configuration (.ini) files and were designed to be run together to demonstrate a complete end-to-end demonstration of the workflow for probabilistic event-based risk calculations.

Hazard
------
* Expected runtime: 4 minutes
* Number of sites: 9144
* Number of logic tree realizations: 1
* GMPEs: ChiouYoungs2008
* IMTs: PGA
* Outputs: Ground Motion Fields, Stochastic Event Sets

Risk
----
* Expected runtime: 3 minutes
* Loss types: Structural, Nonstructural
* Number of taxonomies: 5
* Outputs: Loss Curves, Aggregate Loss Curves, Event Loss Tables, Loss Maps
