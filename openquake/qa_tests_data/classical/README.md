|Test ID|Description|
|-|-|
|case\_01|Test .npz export, raises error when all source are discarded and test wrong .ini|
|case\_02|Test reqv, 1 rlz, 1 site|
|case\_03|Test minimum\_magnitude|
|case\_04|Test UHS|
|case\_05|Test disagg_by_src, individual_rlzs|
|case\_06|Test site\_labels|
|case\_06\_sampling|Test site\_labels with oversampling|
|case\_07|Test DummyGMPE in event_based|
|case\_08|Test override_vs30 with two values and disagg_by_src|
|case\_09|Test ConditionalGMPE Macedo2019|
|case\_12|Two TRTs, 1 rlz|
|case\_18|3 GMPETables|
|case\_22|Test tiling and International Date Line|
|case\_23|Filtering away a TRT|
|case\_24|Test collapsing rjb-independent GMPE|
|case\_25|Test negative depths|
|case\_26|Test YoungsCoppersmith1985MFD|
|case\_27|Nankai mutex model, including disaggregation|
|case\_29|Non-parametric source with one rupture represente by 2 kite surfaces|
|case\_32|Source Specific Logic Tree|
|case\_33|Directivity|
|case\_34|AvgSA|
|case\_35|Test cluster feature|
|case\_37|Christchurch GMPEs|
|case\_38|Example with custom site id and BCHydro GMPEs|
|case\_40|NGAEast GMPEs|
|case\_41|SERA Site Amplification Models including EC8 Site Classes and Geology|
|case\_42|Split/filter a long complex fault source with maxdist=1000 km|
|case\_43|Test for ps grid spacing|
|case\_44|Test for shift hypo feature|
|case\_47|Mixture Model for Sigma using PEER (2018) Test Case 2.5b|
|case\_48|Precise test of pointsource distance|
|case\_49|Test the use of the convolution method to amplify the motion|
|case\_50|Test the use of the kernel method to amplify the motion|
|case\_51|Test the use of a modifiable GMPE|
|case\_53|Tests the modifiable GMPE with imt-independent linear scaling factors on median and standard deviation|
|case\_54|Tests the modifiable GMPE with imt-dependent linear scaling factors on median and standard deviation|
|case\_55|Tests the use of amplification functions|
|case\_57|Test for sampling AvgPoeGMPE|
|case\_60|Test CampbellBozorgnia2003NSHMP2007 and no hazard|
|case\_61|Test KiteFault source and an ESHM20 BCHydro GSIM without a FABA model specified|
|case\_62|Tests a sample model from SHERIFS|
|case\_63|Test for GMM with soiltype|
|case\_64|LanzanoEtAl2016 with bas term|
|case\_65|Test for the multi fault source|
|case\_66|Tests sites slice and site <-> sitemodel association|
|case\_67|Filtered away multiFaultSource|
|case\_68|Check indirect AvgSA GMPEs can still compute non-AvgSA IMTs using underlying GMPE if no AvgSA IMTs in job file|
|case\_69|Collapse area source, 1 site|
|case\_70|Test AbrahamsonGulerce2020|
|case\_71|Test NGAEast (gmpe table) as underlying GSIM when using conditional GMPEs|
|case\_72|Test calculation with a subset of the 2014 US model|
|case\_74|Tests EAS-based calculation|
|case\_75|Tests calculation with multi-fault source|
|case\_75\_pre|Tests preclassical without sitecol for Hamlet|
|case\_76|Tests for Canada SHM6|
|case\_77|Tests Modifiable GMPE with Tabular GMM|
|case\_78|Tests Modifiable GMPE with NegativeBinomialTOM|
|case\_80|Tests New Madrid cluster with rup\_mutex|
|case\_82|tests two mps, only one with reqv that should collapse points|
|case\_83|Tests non-ergodic path effect modifications for Zhao et al. 2016 GMM|
|case\_84|Tests reqv\_ignore\_sources |
|case\_85|Tests conditional gmm MacedoEtAl2019SInter for computation of arias intensity|
|case\_86|Compare direct and indirect AvgSA|
|case\_87|Tests execution of NGAEastUSGSGMPE with Chapman and Guo (2021) coastal plains site amp model|
|case\_88|Tests execution of AtkinsonMacias2009 GMM with BA08 site term specified as input argument|
|case\_89|Tests execution of site model with non-measured (-999) z1pt0 and z2pt5 and basin-param using GMMs|
|case\_90|Tests execution of multiple conditional GMPEs specified within a single ModifiableGMPE|
|case\_91|Check SA and AvgSA with the same ordinal within indirect approach AvgSA are not overwritting each other in dstore|
|case\_92|Tests use of correlation models using EmpiricalAvgSACorrelationModel|
|case\_93|Tests use of GMPE Tables with indirect AvgSA correlation models|
|case\_94|Tests application of deltas to total, tau and phi using mgmpe (both scalar and IMT-dependent)
