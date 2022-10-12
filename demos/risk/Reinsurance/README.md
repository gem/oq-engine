Event-based Risk demo with reinsurance calculation
--------------------------------------------------

In this example we first compute the earthquake ruptures and the
corresponding ground motion fields for the intensity measure
types (IMTs) defined in the vulnerability models, for the sites
of interest defined in the site model.

The GMFs produced in the above step are then used to compute
expected losses for the assets defined in the exposure model, as
well as aggregate losses by the `policy` tag.
Aggregate event loss tables and loss curves are computed for
the entire portfolio.
Reinsurance retention, cession and overspills are computed per
treaty type.

Note: This demo consists of a single job configuration
file (job.ini) that combines the hazard and risk calculations, to
demonstrate a complete end-to-end demonstration of the workflow.

**Expected Runtimes and Outputs**

Expected runtime: <20 seconds

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
- Aggregated Reinsurance Curves
- Average Reinsurance By Policy
- Average Reinsurance
- Reinsurance By Event

