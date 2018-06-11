Event-based PSHA with logic tree sampling
=========================================

============== ===================
checksum32     3,756,725,912      
date           2018-06-05T06:39:59
engine_version 3.2.0-git65c4735   
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
#tot_weight   0    
============= =====

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= =======
source_id source_class num_ruptures calc_time split_time num_sites num_split events 
========= ============ ============ ========= ========== ========= ========= =======
1         AreaSource   2,456        8.00614   0.07272    2.05863   614       509,269
========= ============ ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   8.00614   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00693 0.00267 0.00334 0.01385 56       
compute_ruptures   1.40972 0.54663 0.75848 2.05632 6        
================== ======= ======= ======= ======= =========

Data transfer
-------------
================ ================================================================================ =========
task             sent                                                                             received 
RtreeFilter      srcs=209.74 KB monitor=18.92 KB srcfilter=15.26 KB                               238.34 KB
compute_ruptures sources=210.59 KB param=5.58 KB monitor=2.07 KB gsims=1.88 KB src_filter=1.37 KB 6.98 MB  
================ ================================================================================ =========

Slowest operations
------------------
=============================== ========= ========= ======
operation                       time_sec  memory_mb counts
=============================== ========= ========= ======
total compute_ruptures          8.45834   8.46875   6     
EventBasedRuptureCalculator.run 3.05539   6.88281   1     
managing sources                2.56513   6.75781   1     
making contexts                 1.92244   0.0       2,667 
total prefilter                 0.38819   3.46875   56    
unpickling compute_ruptures     0.25232   0.0       6     
saving ruptures                 0.15619   0.0       6     
reading composite source model  0.14724   0.0       1     
splitting sources               0.14662   0.0       1     
unpickling prefilter            0.03658   0.0       56    
setting event years             0.01873   0.0       1     
store source_info               0.00518   0.0       1     
reading site collection         7.448E-04 0.0       1     
=============================== ========= ========= ======