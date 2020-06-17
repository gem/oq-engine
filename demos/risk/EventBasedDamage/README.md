Stochastic Event-based Damage Demo
--------------------------------

In this example, we first compute the earthquake ruptures and the 
corresponding ground motion fields, for the intensity measure 
types (IMTs) defined in the fragility models, and for the sites
of interest defined in the exposure model.

The gmfs produced in the above step are then used to compute 
expected damage and losses, for the assets defined in the exposure model. 
Aggregate loss cures are also computed for the entire portfolio.

Note: This demo consists of a single job configuration
file (job.ini) that combines the hazard and damage calculations, to
demonstrate a complete end-to-end demonstration of the workflow.


**Expected Runtimes and Outputs**

Expected runtime for event damage calculation: 26 seconds

Hazard outputs:

- Realizations
- Earthquake Ruptures
- Events
- Ground Motion Fields
- Hazard Curves

Damage and loss outputs:

- Aggregate Event Damages
- Aggregate Event Losses
- Average Asset Damages
- Average Asset Damages Statistics
- Average Asset Losses
- Average Asset Losses Statistics
