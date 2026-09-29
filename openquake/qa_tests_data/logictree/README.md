| Test ID     | Description                                                                |
| ----------- | -------------------------------------------------------------------------- |
| case_01     | Same source in two source models                                           |
| case_02     | Test view('inputs')                                                        |
| case_03     | Test ab_max_mag uncertainty                                                |
| case_04     | KOR model, extendModel with bang sources                                   |
| case_05     | Test mean_disagg_by_src                                                    |
| case_05_bis | As above, but with sampling                                                |
| case_06     | Tests two source models with disagg_by_src                                 |
| case_07     | Test 3 source models with a duplicate source, i.e. nontrivial trt_smrs     |
| case_07_bis | Test sampling and .getsources()                                            |
| case_08     | Source Specific Logic Tree on 1 source, the other ignored                  |
| case_09     | Source Specific Logic Tree on 1 source                                     |
| case_10     | Source Specific Logic Tree on 1 source                                     |
| case_11     | Source Specific Logic Tree on 1 source, test disagg_by_src                 |
| case_12     | Test NAF-like model                                                        |
| case_12_bis | Test reduction with empty branches                                         |
| case_13     | 2x2 rlz, duplicated sources, discarding mags                               |
| case_14     | Test 2 gsims and 1 sample                                                  |
| case_15     | Nontrivial source model logic tree with 8+4 realizations                   |
| case_16     | Sampling 10 logic tree paths out of 759_375                                |
| case_17     | Sampling 5 logic tree paths out of 2                                       |
| case_18     | Two GSIMs and 5 samples                                                    |
| case_19     | Test AvgGMPE                                                               |
| case_20     | Nontrivial source model logic tree with 8+4 realizations changing surfaces |
| case_20_bis | Tests mean_rates_by_src                                                    |
| case_21     | Source Specific Logic Tree with 27 realizations                            |
| case_22     | Test sigma_model_alatik2015                                                |
| case_23     | Arctic region and IDL (no bounding box)                                    |
| case_23_bis | Correlated uncertainties                                                   |
| case_28     | Test collapse_gsim_logic_tree                                              |
| case_28_bis | Test missing z1pt0                                                         |
| case_25     | BC Hydro NVA SSC LT source model LT                                        |
| case_26     | 3-branch amp LT with classical for full enumeration and sampling           |
| case_27     | 3-branch amp LT with disagg for full enumeration and sampling              |
| case_29     | Set hypo depth dist epistemic uncertainty                                  |
| case_30     | IMT-dependent weights, International Date Line                             |
| case_31     | Source Specific Logic Tree                                                 |
| case_32     | Tests setAspectRatioAbsolute and setAspectRatioRelative                    |
| case_33     | Tests setLowerSeismDepthRelative and setLowerSeismDepthAbsolute            |
| case_36     | Advanced applyToSources                                                    |
| case_39     | 0-IMT-weights, pointsource distance=0 and ruptures collapsing              |
| case_45     | MMI with disagg_by_src and sampling                                        |
| case_46     | Test applyToBranches                                                       |
| case_52     | late weights vs early weights                                              |
| case_52_bis | late_latin vs early_latin weights                                          |
| case_56     | Sensitivity Analysis on area_source_discretization                         |
| case_58     | Test for the truncatedGRFromSlipAbsolute and geometry uncertainty          |
| case_59     | Test for NRCan15SiteTerm                                                   |
| case_67     | Tricky Source Specific Logic Tree                                          |
| case_68     | Test extendModel                                                           |
| case_68_bis | Test reduction to single source                                            |
| case_71     | Test oversampling                                                          |
| case_73     | Tests some epistemic uncertainties in a source-specific LT                 |
| case_79     | Tests disagg_by_src with semicolon sources                                 |
| case_80     | Tests areaSourceGeometryAbsolute                                           |
| case_83     | Tests extendModel and reqv                                                 |
| case_83_eb  | Double extendModel with event based sampling                               |
| case_84     | Tests maxMagGRRelativeNoMoBalance uncertainty                              |
