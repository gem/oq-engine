Event-based Risk demo with reinsurance calculation
--------------------------------------------------

In this example, we first compute the earthquake ruptures and the 
corresponding ground motion fields, for the intensity measure 
types (IMTs) defined in the vulnerability models, and for the sites
of interest defined in the exposure model.

The gmfs produced in the above step are then used to compute 
expected losses for the assets defined in the exposure model, as
well as aggregation by the `policy` tag.
Aggregate event loss tables and loss cures are computed for 
the entire portfolio and per tag.
Reinsurance retention, cession and overspills are computed per
treaty type. Aggregated loss curves are also produced.

Note: This demo consists of a single job configuration
file (job.ini) that combines the hazard and risk calculations, to
demonstrate a complete end-to-end demonstration of the workflow.


**Expected Runtimes and Outputs**

Expected runtime: 13 seconds

Hazard outputs:

- Realizations
- Earthquake Ruptures
- Events
- Ground Motion Fields

Risk outputs:

- Aggregate Risk Curves Statistics
- Aggregate Risk Statistics
- Aggregated Risk By Event
- Average Asset Losses Statistics
- Source Loss Table
- reinsurance-aggcurves
- reinsurance-aggrisk
- reinsurance-avg_losses
- reinsurance-risk_by_event
