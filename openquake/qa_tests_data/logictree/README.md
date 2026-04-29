| Test ID            | Description                                                                |
| case\_01           | Same source in two source models                                           |
| case\_02           | Test view('inputs')                                                        |
| case\_03           | Test ab_max_mag uncertainty                                                |
| case\_04           | KOR model, extendModel with bang sources                                   |
| case\_05           | Test mean_disagg_by_src                                                    |
| case\_05\_bis      | As above, but with sampling                                                |
| case\_06           | Tests two source models with disagg_by_src                                 |
| case\_07           | Test 3 source models with a duplicate source, i.e. nontrivial trt\_smrs    |
| case\_07\_bis      | Test sampling and .getsources()                                            |
| case\_08           | Source Specific Logic Tree on 1 source, the other ignored                  |
| case\_09           | Source Specific Logic Tree on 1 source                                     |
| case\_10           | Source Specific Logic Tree on 1 source                                     |
| case\_11           | Source Specific Logic Tree on 1 source, test disagg\_by\_src               |
| case\_12           | Test NAF-like model                                                        |
| case\_12\_bis      | Test reduction with empty branches                                         |
| case\_13           | 2x2 rlz, duplicated sources, discarding mags                               |
| case\_14           | Test 2 gsims and 1 sample                                                  |
| case\_15           | Nontrivial source model logic tree with 8+4 realizations                   |
| case\_16           | Sampling 10 logic tree paths out of 759\_375                               |
| case\_17           | Sampling 5 logic tree paths out of 2                                       |
| case\_18           | Two GSIMs and 5 samples                                                    |
| case\_19           | Test AvgGMPE                                                               |
| case\_20           | Nontrivial source model logic tree with 8+4 realizations changing surfaces |
| case\_20\_bis      | Tests mean_rates_by_src                                                    |
| case\_21           | Source Specific Logic Tree with 27 realizations                            |
| case\_22           | Test sigma_model_alatik2015                                                |
| case\_23           | Arctic region and IDL (no bounding box)                                    |
| case\_28           | Test collapse\_gsim\_logic\_tree                                           |
| case\_28\_bis      | Test missing z1pt0                                                         |
| case\_30           | IMT-dependent weights, International Date Line                             |
| case\_31           | Source Specific Logic Tree                                                 |
| case\_32           | Tests setAspectRatioAbsolute and setAspectRatioRelative                    |
| case\_33           | Tests setLowerSeismDepthRelative and setLowerSeismDepthAbsolute            |
| case\_36           | Advanced applyToSources                                                    |
| case\_39           | 0-IMT-weights, pointsource distance=0 and ruptures collapsing              |
| case\_45           | MMI with disagg\_by\_src and sampling                                      |
| case\_46           | Test applyToBranches                                                       |
| case\_52           | late weights vs early weights                                              |
| case\_52\_bis      | late\_latin vs early\_latin weights                                        |
| case\_56           | Sensitivity Analysis on area\_source\_discretization                       |
| case\_58           | Test for the truncatedGRFromSlipAbsolute and geometry uncertainty          |
| case\_59           | Test for NRCan15SiteTerm                                                   |
| case\_67           | Tricky Source Specific Logic Tree                                          |
| case\_68           | Test extendModel                                                           |
| case\_68\_bis      | Test reduction to single source                                            |
| case\_71           | Test oversampling                                                          |
| case\_73           | Tests some epistemic uncertainties in a source-specific LT                 |
| case\_79           | Tests disagg\_by\_src with semicolon sources                               |
| case\_80           | Tests areaSourceGeometryAbsolute                                           |
| case\_83           | Tests extendModel and reqv                                                 |
| case\_84           | Tests maxMagGRRelativeNoMoBalance uncertainty                              |
