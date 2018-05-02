Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     3,360,147,003      
date           2018-04-30T11:22:57
engine_version 3.1.0-gitb0812f0   
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
b3        0.30000 complex(4,5,2,1) 1/1             
========= ======= ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ================= ======================= =================
grp_id gsims                                                                                            distances         siteparams              ruptparams       
====== ================================================================================================ ================= ======================= =================
0      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake         
1      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
4      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake         
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
#tot_weight   0    
============= =====

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
19        SimpleFaultSource 349          0.25492   1.969E-04  108       12        0     
1339      AreaSource        168          0.17473   0.00371    93        12        0     
247       AreaSource        156          0.10709   0.00441    58        13        10    
246       AreaSource        156          0.08081   0.00427    58        13        9     
248       AreaSource        384          0.07217   0.01168    14        7         0     
263       AreaSource        1,022        0.05986   0.02208    11        9         9     
264       AreaSource        1,022        0.05965   0.02203    11        9         9     
20        SimpleFaultSource 31           0.04801   7.629E-05  54        6         0     
257       AreaSource        96           0.04597   0.00316    47        8         5     
258       AreaSource        96           0.04495   0.00302    47        8         8     
259       AreaSource        96           0.04451   0.00301    47        8         8     
249       AreaSource        384          0.04129   0.01169    14        7         0     
250       AreaSource        384          0.03819   0.01165    13        7         0     
22        SimpleFaultSource 34           0.03031   7.272E-05  6         6         0     
330051    PointSource       34           0.01843   9.537E-07  16        1         0     
1         AreaSource        7            0.01810   9.353E-04  5         1         1     
330048    PointSource       28           0.01777   1.431E-06  8         1         0     
330047    PointSource       26           0.01740   1.192E-06  8         1         0     
330045    PointSource       22           0.01737   1.907E-06  7         1         0     
330050    PointSource       28           0.01544   1.192E-06  8         1         0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
AreaSource        0.79757   13    
PointSource       0.31969   51    
SimpleFaultSource 0.34798   4     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
compute_ruptures   0.18932 0.15291 0.03286 0.47111 8        
================== ======= ======= ======= ======= =========

Informational data
------------------
================ ================================================================================ ========
task             sent                                                                             received
compute_ruptures sources=92.43 KB src_filter=47.38 KB param=4.35 KB gsims=3.04 KB monitor=2.58 KB 17.29 KB
================ ================================================================================ ========

Slowest operations
------------------
============================== ======== ========= ======
operation                      time_sec memory_mb counts
============================== ======== ========= ======
total compute_ruptures         1.51454  4.46484   8     
managing sources               0.62029  0.0       1     
reading composite source model 0.18991  0.0       1     
splitting sources              0.10414  0.0       1     
store source_info              0.01499  0.0       1     
saving ruptures                0.01354  0.0       8     
making contexts                0.00586  0.0       3     
setting event years            0.00231  0.0       1     
unpickling compute_ruptures    0.00151  0.0       8     
reading site collection        0.00127  0.0       1     
============================== ======== ========= ======