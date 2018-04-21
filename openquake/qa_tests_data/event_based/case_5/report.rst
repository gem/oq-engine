Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     3,360,147,003      
date           2018-04-19T05:04:15
engine_version 3.1.0-git9c5da5b   
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
========= ====== ================ ================
smlt_path weight gsim_logic_tree  num_realizations
========= ====== ================ ================
b1        0.500  complex(1,5,2,4) 1/1             
b2        0.200  complex(1,5,2,4) 5/5             
b3        0.300  complex(1,5,2,4) 1/1             
========= ====== ================ ================

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
source_models/fs_bg_source_model.xml          1      Stable Shallow Crust 1,645        4,385       
source_models/ss_model_final_250km_Buffer.xml 4      Volcanic             640          640         
============================================= ====== ==================== ============ ============

============= =====
#TRT models   3    
#eff_ruptures 2,299
#tot_ruptures 5,039
#tot_weight   0    
============= =====

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
19        SimpleFaultSource 349          0.212     1.671E-04  72        12        0     
1339      AreaSource        168          0.059     0.002      74        12        0     
246       AreaSource        156          0.048     0.003      41        13        9     
247       AreaSource        156          0.043     0.003      40        12        10    
264       AreaSource        1,022        0.036     0.015      10        9         9     
263       AreaSource        1,022        0.036     0.015      10        9         9     
20        SimpleFaultSource 31           0.031     6.890E-05  36        6         0     
257       AreaSource        96           0.028     0.002      35        8         5     
258       AreaSource        96           0.027     0.002      35        8         8     
259       AreaSource        96           0.026     0.002      35        8         8     
249       AreaSource        384          0.020     0.008      7         6         0     
248       AreaSource        384          0.020     0.008      7         6         0     
250       AreaSource        384          0.020     0.008      6         6         0     
22        SimpleFaultSource 34           0.017     7.606E-05  6         6         0     
330051    PointSource       34           0.014     1.192E-06  12        1         0     
1         AreaSource        7            0.013     6.971E-04  4         1         1     
330048    PointSource       28           0.012     1.192E-06  4         1         0     
330045    PointSource       22           0.012     1.669E-06  4         1         0     
330047    PointSource       26           0.012     1.192E-06  4         1         0     
330050    PointSource       28           0.011     1.192E-06  4         1         0     
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
AreaSource        0.384     13    
PointSource       0.222     51    
SimpleFaultSource 0.269     4     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.155 0.083  0.027 0.257 8        
================== ===== ====== ===== ===== =========

Informational data
------------------
================ =============================================================================== ========
task             sent                                                                            received
compute_ruptures sources=80.56 KB src_filter=47.43 KB param=4.4 KB gsims=3.04 KB monitor=2.58 KB 17.3 KB 
================ =============================================================================== ========

Slowest operations
------------------
============================== ======== ========= ======
operation                      time_sec memory_mb counts
============================== ======== ========= ======
total compute_ruptures         1.242    4.895     8     
managing sources               0.379    0.0       1     
reading composite source model 0.145    0.0       1     
splitting sources              0.070    0.0       1     
store source_info              0.012    0.0       1     
saving ruptures                0.010    0.0       8     
making contexts                0.005    0.0       3     
setting event years            0.002    0.0       1     
unpickling compute_ruptures    0.001    0.0       8     
reading site collection        0.001    0.0       1     
============================== ======== ========= ======