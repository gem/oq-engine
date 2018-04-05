Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     479,109,370        
date           2018-02-02T16:04:04
engine_version 2.9.0-gitd6a3184   
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
b1        0.500  complex(1,2,5,4) 1/1             
b2        0.200  complex(1,2,5,4) 20/20           
b3        0.300  complex(1,2,5,4) 1/1             
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
source_models/fs_bg_source_model.xml          3      Active Shallow Crust 1,008        2,918       
source_models/fs_bg_source_model.xml          4      Stable Shallow Crust 214,741      440,748     
source_models/ss_model_final_250km_Buffer.xml 7      Volcanic             640          640         
============================================= ====== ==================== ============ ============

============= =======
#TRT models   4      
#eff_ruptures 216,473
#tot_ruptures 444,390
#tot_weight   0      
============= =======

Informational data
------------------
========================= =================================================================================
compute_ruptures.received tot 113.57 KB, max_per_task 33.52 KB                                             
compute_ruptures.sent     sources 2.8 MB, src_filter 47.43 KB, param 4.4 KB, gsims 2.96 KB, monitor 2.52 KB
hazard.input_weight       54739.49999999996                                                                
hazard.n_imts             1                                                                                
hazard.n_levels           1                                                                                
hazard.n_realizations     120                                                                              
hazard.n_sites            100                                                                              
hazard.n_sources          142                                                                              
hazard.output_weight      30.0                                                                             
hostname                  tstation.gem.lan                                                                 
require_epsilons          False                                                                            
========================= =================================================================================

Slowest sources
---------------
========= ================= ============ ========= ========= =========
source_id source_class      num_ruptures calc_time num_sites num_split
========= ================= ============ ========= ========= =========
264       AreaSource        3,430        0.0       1         0        
330075    PointSource       16           0.0       1         0        
322       AreaSource        12,288       0.0       1         0        
27        SimpleFaultSource 158          0.0       1         0        
1327      SimpleFaultSource 56           0.0       1         0        
330050    PointSource       28           0.0       1         0        
295       SimpleFaultSource 22           0.0       1         0        
422       SimpleFaultSource 69           0.0       1         0        
318       AreaSource        17,964       0.0       1         0        
330071    PointSource       12           0.0       1         0        
323891    PointSource       6            0.0       1         0        
358       SimpleFaultSource 38           0.0       1         0        
282       SimpleFaultSource 23           0.0       1         0        
246       AreaSource        564          0.0       1         0        
315       AreaSource        476          0.0       1         0        
330079    PointSource       12           0.0       1         0        
323894    PointSource       6            0.0       1         0        
259       AreaSource        348          0.0       1         0        
101623    PointSource       36           0.0       1         0        
330065    PointSource       14           0.0       1         0        
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
================== ===== ====== ===== === =========
operation-duration mean  stddev min   max num_tasks
compute_ruptures   7.016 6.372  0.033 17  8        
================== ===== ====== ===== === =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         56        7.008     8     
reading composite source model 20        0.0       1     
managing sources               18        0.0       1     
store source_info              0.013     0.0       1     
saving ruptures                0.007     0.0       8     
making contexts                0.005     0.0       8     
setting event years            0.002     0.0       1     
reading site collection        6.576E-04 0.0       1     
============================== ========= ========= ======