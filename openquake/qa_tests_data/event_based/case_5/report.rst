Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     3,360,147,003      
date           2018-05-15T04:14:20
engine_version 3.1.0-git0acbc11   
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
====== ================================================================================================ ================= ======================= =================
grp_id gsims                                                                                            distances         siteparams              ruptparams       
====== ================================================================================================ ================= ======================= =================
0      FaccioliEtAl2010()                                                                               rjb rrup          vs30                    mag rake         
1      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
4      FaccioliEtAl2010()                                                                               rjb rrup          vs30                    mag rake         
====== ================================================================================================ ================= ======================= =================

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
#tot_ruptures 5,039
#tot_weight   898  
============= =====

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
19        SimpleFaultSource 10           0.23458   0.0        108       12        0     
264       PointSource       14           0.15631   0.0        11        9         0     
1339      PointSource       14           0.13061   0.0        93        12        0     
263       PointSource       14           0.09095   0.0        11        9         0     
247       PointSource       12           0.08767   0.0        58        13        10    
20        SimpleFaultSource 2            0.07786   0.0        54        6         0     
246       PointSource       12           0.07356   0.0        58        13        9     
250       PointSource       12           0.06395   0.0        13        7         0     
257       PointSource       12           0.05977   0.0        47        8         5     
248       PointSource       12           0.05767   0.0        14        7         0     
258       PointSource       12           0.04818   0.0        47        8         8     
259       PointSource       12           0.04628   0.0        47        8         8     
249       PointSource       12           0.04623   0.0        14        7         0     
330045    PointSource       22           0.03568   0.0        7         1         0     
330047    PointSource       26           0.03038   0.0        8         1         0     
330048    PointSource       28           0.02978   0.0        8         1         0     
330046    PointSource       20           0.02597   0.0        5         1         0     
330051    PointSource       34           0.02563   0.0        16        1         0     
330050    PointSource       28           0.02509   0.0        8         1         0     
22        SimpleFaultSource 2            0.02400   0.0        6         6         0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
PointSource       1.30530   64    
SimpleFaultSource 0.34782   4     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00898 0.01403 0.00217 0.06761 55       
compute_ruptures   0.14541 0.12032 0.00277 0.42428 13       
================== ======= ======= ======= ======= =========

Informational data
------------------
================ ================================================================================= =========
task             sent                                                                              received 
prefilter        srcs=188.61 KB monitor=17.35 KB srcfilter=12.3 KB                                 118.06 KB
compute_ruptures sources=146.23 KB src_filter=77.01 KB param=7.07 KB gsims=5.03 KB monitor=4.19 KB 18.46 KB 
================ ================================================================================= =========

Slowest operations
------------------
============================== ======== ========= ======
operation                      time_sec memory_mb counts
============================== ======== ========= ======
total compute_ruptures         1.89027  1.82422   13    
managing sources               0.67931  0.0       1     
total prefilter                0.49371  4.57422   55    
reading composite source model 0.24469  0.0       1     
splitting sources              0.09653  0.0       1     
saving ruptures                0.01018  0.0       13    
store source_info              0.00910  0.0       1     
unpickling prefilter           0.00685  0.0       55    
making contexts                0.00616  0.0       3     
setting event years            0.00141  0.0       1     
unpickling compute_ruptures    0.00139  0.0       13    
reading site collection        0.00128  0.0       1     
============================== ======== ========= ======