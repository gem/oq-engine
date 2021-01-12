Stochastic Event-based Risk Demo
--------------------------------

In this example, we first compute the earthquake ruptures and the 
corresponding ground motion fields, for the intensity measure 
types (IMTs) defined in the vulnerability models, and for the sites
of interest defined in the exposure model.

The gmfs produced in the above step are then used to compute 
expected losses and loss maps for 10% and 2% probabilities of 
exceedance in 50 years, for the assets defined in the exposure model. 
Aggregate loss cures are also computed for the entire portfolio.

Note: This demo consists of a single job configuration
file (job.ini) that combines the hazard and risk calculations, to
demonstrate a complete end-to-end demonstration of the workflow.

An alternate file, job_eb.ini, is also included in this demo, to
demonstrate the newer `ebrisk` calculator.


**Expected Runtimes and Outputs**

Expected runtime for hazard calculation: 10 seconds

Hazard outputs:

- Realizations
- Earthquake Ruptures
- Events
- Ground Motion Fields
- Hazard Curves

Expected runtime for risk calculation: 40 seconds

Risk outputs:

- Aggregate Event Losses
- Aggregate Loss Curves
- Aggregate Loss Curves Statistics
- Asset Loss Curves Statistics
- Asset Loss Maps
- Asset Loss Maps Statistics
- Average Asset Losses
- Average Asset Losses Statistics
