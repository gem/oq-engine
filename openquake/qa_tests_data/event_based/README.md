
| Test ID | Description |
|---------|-------------|
| case_1  | Test the use of IMT-dependent weights in the GMC logic tree | 
| case_2  | Test the use of a rather small discretisation for MFDs | 
| case_3  | Source model with one point source The GMC LT contains two GMMs | 
| case_4  | Source model with one simple fault source | 
| case_5  | Test the option of discarding some TR using the `job.ini` file. See example [here](https://github.com/gem/oq-engine/blob/20200312_table/openquake/qa_tests_data/event_based/case_5/job.ini#L33s)  | 
| case_6  | Check we calculate only hazard curves | 
| case_7  | Test a simple case with logic tree sampling | 
| case_8  | Test EB with a non-parametric source | 
| case_9  | Test EB hazard for San-Jose (CRI) with a reduced model | 
| case_10 | Test EB hazard for Bogota (COL) with a reduced model | 
| case_11 | *missing :^)* |
| case_12 | Test a SSM with sources from 2 TRs | 
| case_13 | *unclear* | 
| case_14 | Test calculation for South Africa | 
| case_15 | Test calculation using a reduced model similar to the Japan one | 
| case_16 | Test calculation using a reduced model similar to the Italy one | 
| case_17 | Test a simple case with logic tree sampling *check this* | 
| case_18 | *unclear* | 
| case_19 | Test EB hazard for Vancouver (CAN) with a reduced model | 
| case_20 | Test EB hazard for Vancouver (CAN) with a reduced model + site conditions | 
| case_21 | Test the use of a source model containing a cluster | 
| case_22 | Test the use of the [SplitSigmaGMPE](https://github.com/gem/oq-engine/blob/master/openquake/hazardlib/gsim/mgmpe/split_sigma_gmpe.py) modifiable GMPE | 
| case_23 | Test the definition of the region of investigation from the exposure model | 
| case_24 | Test the use of the `shift_hypo` option in the `job.ini` | 
| case_25 | Test the use of multiple files for the definition of a source models | 
| mutex   | Test the use of a source model with mutually exclusive sources | 
| spatial_correlation | Test the use spatial_correlation for the calculation of GMFs | 
