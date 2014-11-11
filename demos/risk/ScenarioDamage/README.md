Scenario Damage Demo
====================

In this example, we start with a single rupture definition, and compute a set of ground motion fields for the sites of interest defined in the exposure model. The aleatory uncertainty in the ground motion values is considered by sampling multiple realizations of the ground motion field.

The ground motion fields produced in the above step are then used to compute the distribution of damage for the assets defined in the exposure model. The damage distribution per building taxonomy and the total damage distribution are also computed.

Note: This calculation demo consists of two parts: hazard and risk. The hazard and risk calculations are defined in separate job configuration (.ini) files and were designed to be run together to demonstrate a complete end-to-end demonstration of the workflow for scenario damage calculations.

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
* Expected runtime: 5 minutes
* Outputs: Damage Distribution per Asset, Damage Distribution per Taxonomy, Total Damage Distribution, Collapse Maps