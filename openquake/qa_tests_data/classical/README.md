| Test ID | Description                                                                                            |
|---------|--------------------------------------------------------------------------------------------------------|
| case_01 | Test .npz export, raises error when all source are discarded and test wrong .ini                       |
| case_02 | Test reqv, 1 rlz, 1 site                                                                               |
| case_12 | Two TRTs, 1 rlz                                                                                        |
| case_14 | Test reqv                                                                                              |
| case_18 | 3 GMPETables                                                                                           |
| case_22 | Test tiling and International Date Line                                                                |
| case_23 | Filtering away a TRT                                                                                   |
| case_24 | Test collapsing rjb-independent GMPE                                                                   |
| case_25 | Test negative depths                                                                                   |
| case_26 | Test YoungsCoppersmith1985MFD                                                                          |
| case_27 | Nankai mutex model, including disaggregation                                                           |
| case_29 | Non-parametric source with one rupture represente by 2 kite surfaces                                   |
| case_30 | IMT-dependent weights, sampling with cheating                                                          |
| case_32 | Source Specific Logic Tree                                                                             |
| case_33 | Directivity                                                                                            |
| case_34 | AvgSA                                                                                                  |
| case_35 | Test cluster feature                                                                                   |
| case_37 | Christchurch GMPEs                                                                                     |
| case_38 | Example with custom_site_id and BCHydro GMPEs                                                          |
| case_39 | 0-IMT-weights, pointsource_distance=0 and ruptures collapsing                                          |
| case_40 | NGAEast GMPEs                                                                                          |
| case_41 | SERA Site Amplification Models including EC8 Site Classes and Geology                                  |
| case_42 | Split/filter a long complex fault source with maxdist=1000 km                                          |
| case_43 | Test for ps_grid_spacing                                                                               |
| case_44 | Test for shift_hypo feature                                                                            |
| case_47 | Mixture Model for Sigma using PEER (2018) Test Case 2.5b                                               |
| case_48 | Precise test of pointsource_distance                                                                   |
| case_49 | Test the use of the convolution method to amplify the motion                                           |
| case_50 | Test the use of the kernel method to amplify the motion                                                |
| case_51 | Test the use of a modifiable GMPE                                                                      |
| case_52 |                                                                                                        |
| case_53 | Tests the modifiable GMPE with imt-independent linear scaling factors on median and standard deviation |
| case_54 | Tests the modifiable GMPE with imt-dependent linear scaling factors on median and standard deviation   |
| case_55 | Tests the use of amplification functions                                                               |
| case_57 | Test for sampling AvgPoeGMPE                                                                           |
| case_60 | Test CampbellBozorgnia2003NSHMP2007 and no hazard                                                      |
| case_61 | Test KiteFault source                                                                                  |
| case_62 | Tests a sample model from SHERIFS                                                                      |
| case_63 | Test for GMM with soiltype                                                                             |
| case_64 | LanzanoEtAl2016 with bas term                                                                          |
| case_65 | Test for the multi fault source                                                                        |
| case_66 | Tests sites_slice and site <-> sitemodel association                                                   |
| case_69 | Collapse area source, 1 site                                                                           |
| case_70 | Test abrahamson_gulerce_2020                                                                           |
| case_72 | Test calculation with a subset of the 2014 US model                                                    |
| case_74 | Tests EAS-based calculation                                                                            |
| case_75 | Tests calculation with multi-fault source                                                              |
| case_76 | Tests for Canada SHM6                                                                                  |
| case_77 | Tests Modifiable GMPE with Tabular GMM                                                                 |
| case_82 | tests two mps, only one with reqv that should collapse points					   |
| case_83 | Tests non-ergodic path effect modifications for Zhao et al. 2016 GMM                                   |      
| case_87 | Tests execution of NGAEastUSGSGMPE with Chapman and Guo (2021) coastal plains site amp model           |
| case_88 | Tests execution of AtkinsonMacias2009 GMM with BA08 site term specified as input argument              |
| case_89 | Tests execution of site model with non-measured (-999) z1pt0 and z2pt5 and basin-param using GMMs      |