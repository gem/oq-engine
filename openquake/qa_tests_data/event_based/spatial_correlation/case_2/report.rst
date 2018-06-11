Probabilistic Event-Based QA Test with Spatial Correlation, case 2
==================================================================

============== ===================
checksum32     1,685,911,934      
date           2018-06-05T06:39:48
engine_version 3.2.0-git65c4735   
============== ===================

num_sites = 2, num_levels = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         150               
truncation_level                None              
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        123456789         
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
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
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         PointSource  1            0.02521   8.106E-06  2.00000   1         22,566
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.02521   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =========
operation-duration mean    stddev min     max     num_tasks
RtreeFilter        0.00104 NaN    0.00104 0.00104 1        
compute_ruptures   0.03267 NaN    0.03267 0.03267 1        
================== ======= ====== ======= ======= =========

Data transfer
-------------
================ ====================================================================== =========
task             sent                                                                   received 
RtreeFilter      srcs=0 B srcfilter=0 B monitor=0 B                                     1.28 KB  
compute_ruptures sources=1.34 KB param=571 B monitor=353 B src_filter=233 B gsims=131 B 575.03 KB
================ ====================================================================== =========

Slowest operations
------------------
=============================== ========= ========= ======
operation                       time_sec  memory_mb counts
=============================== ========= ========= ======
EventBasedRuptureCalculator.run 0.62894   0.0       1     
managing sources                0.36551   0.0       1     
saving ruptures                 0.12392   0.0       1     
setting event years             0.04461   0.0       1     
total compute_ruptures          0.03267   7.19531   1     
store source_info               0.00442   0.0       1     
reading composite source model  0.00331   0.0       1     
unpickling compute_ruptures     0.00117   0.0       1     
total prefilter                 0.00104   0.0       1     
making contexts                 9.930E-04 0.0       1     
reading site collection         7.887E-04 0.0       1     
splitting sources               3.455E-04 0.0       1     
unpickling prefilter            3.047E-04 0.0       1     
=============================== ========= ========= ======