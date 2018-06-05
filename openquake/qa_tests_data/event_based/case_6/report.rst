Event-based PSHA producing hazard curves only
=============================================

============== ===================
checksum32     3,219,914,866      
date           2018-06-05T06:39:43
engine_version 3.2.0-git65c4735   
============== ===================

num_sites = 1, num_levels = 5

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         300               
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
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
b11       0.60000 simple(3)       3/3             
b12       0.40000 simple(3)       3/3             
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

  <RlzsAssoc(size=6, rlzs=6)
  0,BooreAtkinson2008(): [0]
  0,CampbellBozorgnia2008(): [1]
  0,ChiouYoungs2008(): [2]
  1,BooreAtkinson2008(): [3]
  1,CampbellBozorgnia2008(): [4]
  1,ChiouYoungs2008(): [5]>

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
1         AreaSource   2,456        10        0.05895    1.00000   614       912,706
========= ============ ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   10        1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00738 0.00362 0.00217 0.02047 56       
compute_ruptures   1.80154 0.92913 0.71707 3.13518 6        
================== ======= ======= ======= ======= =========

Data transfer
-------------
================ ================================================================================ ========
task             sent                                                                             received
RtreeFilter      srcs=209.74 KB monitor=18.92 KB srcfilter=15.26 KB                               235.8 KB
compute_ruptures sources=208.06 KB param=3.58 KB monitor=2.07 KB gsims=1.88 KB src_filter=1.37 KB 10.48 MB
================ ================================================================================ ========

Slowest operations
------------------
=============================== ========= ========= ======
operation                       time_sec  memory_mb counts
=============================== ========= ========= ======
total compute_ruptures          10        7.23438   6     
EventBasedRuptureCalculator.run 4.11724   0.0       1     
managing sources                3.63100   0.0       1     
making contexts                 2.23564   0.0       3,081 
total prefilter                 0.41347   3.46875   56    
unpickling compute_ruptures     0.28400   0.0       6     
saving ruptures                 0.17958   0.0       6     
reading composite source model  0.12352   0.0       1     
splitting sources               0.11888   0.0       1     
unpickling prefilter            0.04150   0.0       56    
setting event years             0.03338   0.0       1     
store source_info               0.00497   0.0       1     
reading site collection         7.036E-04 0.0       1     
=============================== ========= ========= ======