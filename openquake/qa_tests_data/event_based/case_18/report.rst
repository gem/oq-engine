Event-Based Hazard QA Test, Case 18
===================================

============== ===================
checksum32     2,389,156,703      
date           2018-06-05T06:39:52
engine_version 3.2.0-git65c4735   
============== ===================

num_sites = 1, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    3                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         350               
truncation_level                0.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.001             
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1064              
master_seed                     0                 
ses_seed                        1064              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `three_gsim_logic_tree.xml <three_gsim_logic_tree.xml>`_    
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.33333 simple(3)       3/3             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================== ================= ======================= =================
grp_id gsims                                                    distances         siteparams              ruptparams       
====== ======================================================== ================= ======================= =================
0      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ======================================================== ================= ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=3)
  0,AkkarBommer2010(): [0 2]
  0,ChiouYoungs2008(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3,000        3,000       
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  3,000        6.85291   6.676E-06  1.00000   1         6     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  6.85291   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =========
operation-duration mean    stddev min     max     num_tasks
RtreeFilter        0.00554 NaN    0.00554 0.00554 1        
compute_ruptures   6.86043 NaN    6.86043 6.86043 1        
================== ======= ====== ======= ======= =========

Data transfer
-------------
================ ======================================================================= ========
task             sent                                                                    received
RtreeFilter      srcs=0 B srcfilter=0 B monitor=0 B                                      13.02 KB
compute_ruptures sources=13.07 KB param=604 B monitor=353 B gsims=310 B src_filter=233 B 7.77 KB 
================ ======================================================================= ========

Slowest operations
------------------
=============================== ========= ========= ======
operation                       time_sec  memory_mb counts
=============================== ========= ========= ======
EventBasedRuptureCalculator.run 7.18744   0.0       1     
managing sources                7.05450   0.0       1     
total compute_ruptures          6.86043   7.02344   1     
reading composite source model  0.00891   0.0       1     
saving ruptures                 0.00800   0.0       1     
store source_info               0.00779   0.0       1     
total prefilter                 0.00554   0.0       1     
making contexts                 0.00378   0.0       6     
setting event years             0.00202   0.0       1     
unpickling compute_ruptures     0.00178   0.0       1     
reading site collection         7.367E-04 0.0       1     
splitting sources               3.116E-04 0.0       1     
unpickling prefilter            2.940E-04 0.0       1     
=============================== ========= ========= ======