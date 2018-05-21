Event-based PSHA with logic tree sampling
=========================================

============== ===================
checksum32     3,756,725,912      
date           2018-05-15T04:14:14
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 3, num_levels = 38

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    10                
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         40                
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        23                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b11       0.10000 simple(3)       4/3             
b12       0.10000 simple(3)       6/3             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ============================= =================
grp_id gsims                                                         distances   siteparams                    ruptparams       
====== ============================================================= =========== ============================= =================
0      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
1      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
====== ============================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=10)
  0,BooreAtkinson2008(): [1]
  0,CampbellBozorgnia2008(): [2]
  0,ChiouYoungs2008(): [0 3]
  1,BooreAtkinson2008(): [4 5 6 7 9]
  1,CampbellBozorgnia2008(): [8]>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== ============ ============
source_model      grp_id trt                  eff_ruptures tot_ruptures
================= ====== ==================== ============ ============
source_model1.xml 0      Active Shallow Crust 2,456        2,456       
source_model2.xml 1      Active Shallow Crust 2,456        2,456       
================= ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 4,912
#tot_ruptures 4,912
#tot_weight   491  
============= =====

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= =======
source_id source_class num_ruptures calc_time split_time num_sites num_split events 
========= ============ ============ ========= ========== ========= ========= =======
1         PointSource  8            8.10933   0.0        1,264     614       521,838
========= ============ ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  8.10933   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00716 0.00350 0.00241 0.01957 56       
compute_ruptures   1.41753 0.54135 0.63015 2.12780 6        
================== ======= ======= ======= ======= =========

Informational data
------------------
================ ================================================================================ =========
task             sent                                                                             received 
prefilter        srcs=209.74 KB monitor=17.66 KB srcfilter=12.52 KB                               238.34 KB
compute_ruptures sources=152.46 KB param=5.47 KB src_filter=4.83 KB monitor=1.93 KB gsims=1.88 KB 7.3 MB   
================ ================================================================================ =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         8.50517   4.91016   6     
managing sources               2.49219   0.0       1     
making contexts                2.19016   0.0       2,667 
total prefilter                0.40072   3.37109   56    
unpickling compute_ruptures    0.26496   0.0       6     
saving ruptures                0.16691   0.0       6     
reading composite source model 0.15130   0.0       1     
splitting sources              0.15096   0.0       1     
setting event years            0.01985   0.0       1     
unpickling prefilter           0.01374   0.0       56    
store source_info              0.00476   0.0       1     
reading site collection        3.283E-04 0.0       1     
============================== ========= ========= ======