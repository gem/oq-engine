Scenario Risk Demo
==================

In this example, we start with a single rupture definition, and compute a set of ground motion fields for the sites of interest defined in the exposure model. The aleatory uncertainty in the ground motion values is considered by sampling multiple realizations of the ground motion field.

The ground motion fields produced in the above step are then used to compute the mean and standard deviation of the scenario loss for the assets defined in the exposure model. The mean and standard deviation of the aggregate loss across the entire portfolio are also computed.

Note: This calculation demo consists of two parts: hazard and risk. The hazard and risk calculations are defined in separate job configuration (.ini) files and were designed to be run together to demonstrate a complete end-to-end demonstration of the workflow for scenario risk calculations.

Hazard
------
* Expected runtime: 5 minutes
* Number of sites: 9144
* Number of GMFs: 1000
* GMPEs: ChiouYoungs2008
* IMTs: PGA
* Outputs: Ground Motion Fields

Risk
----
* Expected runtime: 3 minutes
* Loss types: Structural, Nonstructural, Occupants
* Number of taxonomies: 5
* Outputs: Loss Maps, Aggregate Losses