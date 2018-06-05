Event-Based Hazard QA Test, Case 4
==================================

============== ===================
checksum32     3,199,478,063      
date           2018-06-05T06:39:51
engine_version 3.2.0-git65c4735   
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         50                
truncation_level                0.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1066              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 5            5           
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
1         SimpleFaultSource 5            0.00792   1.955E-05  1.00000   1         56    
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.00792   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =========
operation-duration mean    stddev min     max     num_tasks
RtreeFilter        0.00213 NaN    0.00213 0.00213 1        
compute_ruptures   0.01630 NaN    0.01630 0.01630 1        
================== ======= ====== ======= ======= =========

Data transfer
-------------
================ ====================================================================== ========
task             sent                                                                   received
RtreeFilter      srcs=0 B srcfilter=0 B monitor=0 B                                     1.22 KB 
compute_ruptures sources=1.27 KB param=595 B monitor=353 B src_filter=233 B gsims=120 B 6.18 KB 
================ ====================================================================== ========

Slowest operations
------------------
=============================== ========= ========= ======
operation                       time_sec  memory_mb counts
=============================== ========= ========= ======
EventBasedRuptureCalculator.run 0.38900   0.0       1     
managing sources                0.23221   0.0       1     
total compute_ruptures          0.01630   7.08594   1     
saving ruptures                 0.00571   0.0       1     
store source_info               0.00544   0.0       1     
reading composite source model  0.00518   0.0       1     
total prefilter                 0.00213   0.0       1     
setting event years             0.00173   0.0       1     
making contexts                 0.00126   0.0       5     
unpickling compute_ruptures     9.677E-04 0.0       1     
reading site collection         8.805E-04 0.0       1     
splitting sources               3.302E-04 0.0       1     
unpickling prefilter            2.968E-04 0.0       1     
=============================== ========= ========= ======