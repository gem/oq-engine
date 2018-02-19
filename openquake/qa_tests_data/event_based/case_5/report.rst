Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     479,109,370        
date           2018-02-19T09:59:57
engine_version 2.9.0-gitb536198   
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
area_source_discretization      10.0             
ground_motion_correlation_model None             
random_seed                     42               
master_seed                     0                
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
b1        0.500  complex(4,1,5,2) 1/1             
b2        0.200  complex(4,1,5,2) 20/20           
b3        0.300  complex(4,1,5,2) 1/1             
========= ====== ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ================= ======================= ============================
grp_id gsims                                                                                            distances         siteparams              ruptparams                  
====== ================================================================================================ ================= ======================= ============================
1      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake                    
3      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc()                       rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
4      AkkarBommer2010() Campbell2003SHARE() CauzziFaccioli2008() ChiouYoungs2008() ToroEtAl2002SHARE() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor           
7      FaccioliEtAl2010()                                                                               rrup              vs30                    mag rake                    
====== ================================================================================================ ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=11, rlzs=22)
  1,FaccioliEtAl2010(): [0]
  3,AkkarBommer2010(): [1 2 3 4 5]
  3,CauzziFaccioli2008(): [ 6  7  8  9 10]
  3,ChiouYoungs2008(): [11 12 13 14 15]
  3,ZhaoEtAl2006Asc(): [16 17 18 19 20]
  4,AkkarBommer2010(): [ 1  6 11 16]
  4,Campbell2003SHARE(): [ 5 10 15 20]
  4,CauzziFaccioli2008(): [ 2  7 12 17]
  4,ChiouYoungs2008(): [ 3  8 13 18]
  4,ToroEtAl2002SHARE(): [ 4  9 14 19]
  7,FaccioliEtAl2010(): [21]>

Number of ruptures per tectonic region type
-------------------------------------------
============================================= ====== ==================== ============ ============
source_model                                  grp_id trt                  eff_ruptures tot_ruptures
============================================= ====== ==================== ============ ============
source_models/as_model.xml                    1      Volcanic             84           84          
source_models/fs_bg_source_model.xml          3      Active Shallow Crust 324          2,918       
source_models/fs_bg_source_model.xml          4      Stable Shallow Crust 127,791      440,748     
source_models/ss_model_final_250km_Buffer.xml 7      Volcanic             640          640         
============================================= ====== ==================== ============ ============

============= =======
#TRT models   4      
#eff_ruptures 128,839
#tot_ruptures 444,390
#tot_weight   0      
============= =======

Informational data
------------------
========================= ==================================================================================
compute_ruptures.received tot 141.01 KB, max_per_task 34.22 KB                                              
compute_ruptures.sent     sources 3.31 MB, src_filter 53.36 KB, param 4.95 KB, gsims 3.42 KB, monitor 2.8 KB
hazard.input_weight       54739.49999999996                                                                 
hazard.n_imts             1                                                                                 
hazard.n_levels           1                                                                                 
hazard.n_realizations     120                                                                               
hazard.n_sites            100                                                                               
hazard.n_sources          142                                                                               
hazard.output_weight      30.0                                                                              
hostname                  tstation.gem.lan                                                                  
require_epsilons          False                                                                             
========================= ==================================================================================

Slowest sources
---------------
========= ================= ============ ========= ========= =========
source_id source_class      num_ruptures calc_time num_sites num_split
========= ================= ============ ========= ========= =========
330072    PointSource       14           0.0       1         0        
330059    PointSource       14           0.0       1         0        
330       AreaSource        2,256        0.0       1         0        
258       AreaSource        348          0.0       1         0        
1         AreaSource        42           0.0       1         0        
330050    PointSource       28           0.0       1         0        
320       AreaSource        516          0.0       1         0        
345       SimpleFaultSource 35           0.0       1         0        
330048    PointSource       28           0.0       1         0        
330055    PointSource       24           0.0       1         0        
323947    PointSource       6            0.0       1         0        
1339      AreaSource        574          0.0       1         0        
330056    PointSource       12           0.0       1         0        
111       SimpleFaultSource 32           0.0       1         0        
357       SimpleFaultSource 50           0.0       1         0        
323       AreaSource        12,288       0.0       1         0        
330052    PointSource       22           0.0       1         0        
330080    PointSource       12           0.0       1         0        
323893    PointSource       6            0.0       1         0        
317       AreaSource        17,964       0.0       1         0        
========= ================= ============ ========= ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
AreaSource        0.0       50    
PointSource       0.0       51    
SimpleFaultSource 0.0       40    
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   4.033 4.351  0.049 8.802 9        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         36        6.895     9     
managing sources               22        0.0       1     
reading composite source model 20        0.0       1     
store source_info              0.017     0.0       1     
saving ruptures                0.012     0.0       9     
making contexts                0.005     0.0       5     
setting event years            0.003     0.0       1     
reading site collection        4.940E-04 0.0       1     
============================== ========= ========= ======