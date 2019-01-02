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

Note: This calculation demo consists of two parts: hazard and risk. 
The hazard and risk calculations are defined in separate job c
onfiguration (.ini) files and were designed to be run together to
 demonstrate a complete end-to-end demonstration of the workflow.

**Hazard**
Expected runtime: 30 seconds
Outputs: 
		Earthquake Ruptures
		Ground Motion Fields
		Hazard Curves
		Realizations
		Seismic Source Groups

**Risk**
Expected runtime: 40 seconds
Outputs:
		Aggregate Loss Curves
		Aggregate Loss Curves Statistics
		Aggregate Loss Table
		Asset Loss Maps
		Asset Loss Maps Statistics
		Average Asset Losses
		Average Asset Losses Statistics
		Realizations
		Seismic Source Groups
