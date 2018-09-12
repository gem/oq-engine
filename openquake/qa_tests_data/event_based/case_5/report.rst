Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     3,726,424,986      
date           2018-09-05T10:03:57
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 100, num_levels = 1

Parameters
----------
=============================== =================
calculation_mode                'event_based'    
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              30.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            5.0              
complex_fault_mesh_spacing      5.0              
width_of_mfd_bin                0.1              
area_source_discretization      18.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     42               
master_seed                     0                
ses_seed                        23               
=============================== =================

Input files
-----------
======================= ==============================================================================
Name                    File                                                                          
======================= ==============================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                                          
sites                   `sites.csv <sites.csv>`_                                                      
source                  `as_model.xml <as_model.xml>`_                                                
source                  `fs_bg_source_model.xml <fs_bg_source_model.xml>`_                            
source                  `ss_model_final_250km_Buffer.xml <ss_model_final_250km_Buffer.xml>`_          
source_model_logic_tree `combined_logic-tree-source-model.xml <combined_logic-tree-source-model.xml>`_
======================= ==============================================================================

Composite source model
----------------------
========= ======= ================ ================
smlt_path weight  gsim_logic_tree  num_realizations
========= ======= ================ ================
b1        0.50000 complex(4,5,2,1) 1/1             
b2        0.20000 complex(4,5,2,1) 5/5             
b3        0.30000 complex(4,5,2,1) 1/8             
========= ======= ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ================= ======================= ============================
grp_id gsims                                                                                            distances         siteparams              ruptparams                  
====== ================================================================================================ ================= ======================= ============================
0      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake                    
1      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor           
2      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc()                       rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
3      Campbell2003SHARE() ToroEtAl2002SHARE()                                                          rjb rrup                                  mag rake                    
4      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake                    
====== ================================================================================================ ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=7, rlzs=7)
  0,FaccioliEtAl2010(): [0]
  1,AkkarBommer2010(): [1]
  1,Campbell2003SHARE(): [5]
  1,CauzziFaccioli2008(): [2]
  1,ChiouYoungs2008(): [3]
  1,ToroEtAl2002SHARE(): [4]
  4,FaccioliEtAl2010(): [6]>

Number of ruptures per tectonic region type
-------------------------------------------
============================================= ====== ==================== ============ ============
source_model                                  grp_id trt                  eff_ruptures tot_ruptures
============================================= ====== ==================== ============ ============
source_models/as_model.xml                    0      Volcanic             14           14          
source_models/fs_bg_source_model.xml          1      Stable Shallow Crust 1,693        4,385       
source_models/ss_model_final_250km_Buffer.xml 4      Volcanic             640          640         
============================================= ====== ==================== ============ ============

============= =====
#TRT models   3    
#eff_ruptures 2,347
#tot_ruptures 5,192
#tot_weight   0    
============= =====

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
19        SimpleFaultSource 349          0.18751   1.621E-04  9.00000   12        0     
246       AreaSource        156          0.10473   0.00349    4.46154   13        1     
264       AreaSource        1,022        0.09952   0.01812    1.22222   9         0     
1339      AreaSource        168          0.09803   0.00306    7.75000   12        0     
263       AreaSource        1,022        0.09647   0.01763    1.22222   9         0     
259       AreaSource        96           0.07879   0.00232    5.87500   8         0     
250       AreaSource        384          0.07017   0.00944    1.85714   7         0     
249       AreaSource        384          0.06633   0.00935    2.00000   7         0     
247       AreaSource        156          0.06620   0.00359    4.46154   13        0     
258       AreaSource        96           0.05496   0.00226    5.87500   8         0     
257       AreaSource        96           0.05461   0.00254    5.87500   8         1     
248       AreaSource        384          0.05343   0.00884    2.00000   7         0     
20        SimpleFaultSource 31           0.02183   6.676E-05  9.00000   6         0     
330048    PointSource       28           0.02140   7.153E-07  8.00000   1         0     
330047    PointSource       26           0.02083   7.153E-07  8.00000   1         0     
22        SimpleFaultSource 34           0.01892   6.247E-05  1.00000   6         0     
330045    PointSource       22           0.01851   9.537E-07  7.00000   1         0     
330051    PointSource       34           0.01601   7.153E-07  16        1         0     
330046    PointSource       20           0.01581   7.153E-07  5.00000   1         0     
330054    PointSource       30           0.01370   9.537E-07  8.00000   1         0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
AreaSource        0.85833   13    
PointSource       0.32567   51    
SimpleFaultSource 0.23665   4     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ======= ======= =========
operation-duration   mean    stddev    min     max     num_tasks
pickle_source_models 0.05349 0.05870   0.01185 0.12063 3        
preprocess           0.09723 0.09710   0.00117 0.38895 19       
compute_gmfs         0.00468 2.662E-04 0.00449 0.00487 2        
==================== ======= ========= ======= ======= =========

Data transfer
-------------
==================== ============================================================================================= =========
task                 sent                                                                                          received 
pickle_source_models monitor=927 B converter=867 B fnames=608 B                                                    547 B    
preprocess           srcs=148.22 KB param=18.33 KB monitor=5.92 KB srcfilter=4.69 KB                               105.96 KB
compute_gmfs         sources_or_ruptures=8.84 KB param=6.21 KB rlzs_by_gsim=1.04 KB monitor=614 B src_filter=440 B 6.03 KB  
==================== ============================================================================================= =========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total preprocess           1.84745   0.69141   19    
total pickle_source_models 0.16047   1.14062   3     
splitting sources          0.08373   0.0       1     
saving ruptures            0.00968   0.0       3     
total compute_gmfs         0.00935   0.0       2     
store source_info          0.00758   0.0       1     
building ruptures          0.00644   0.0       2     
managing sources           0.00332   0.0       1     
making contexts            0.00281   0.0       3     
GmfGetter.init             0.00117   0.0       2     
aggregating hcurves        3.901E-04 0.0       2     
========================== ========= ========= ======