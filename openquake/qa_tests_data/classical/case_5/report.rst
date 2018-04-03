Classical Hazard QA Test, Case 5
================================

============== ===================
checksum32     2,343,185,032      
date           2018-03-26T15:56:12
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.01              
complex_fault_mesh_spacing      0.1               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
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
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  trivial(1)      1/1             
========= ====== =============== ================

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
source_model.xml 0      Active Shallow Crust 49           49          
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ================== ============ ========= ========== ========= =========
source_id source_class       num_ruptures calc_time split_time num_sites num_split
========= ================== ============ ========= ========== ========= =========
1         ComplexFaultSource 49           0.005     7.391E-06  1         1        
========= ================== ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.005     1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.007 NaN    0.007 0.007 1        
================== ===== ====== ===== ===== =========

Informational data
------------------
============== ===================================================================== ========
task           sent                                                                  received
count_ruptures sources=1.14 KB srcfilter=722 B param=418 B monitor=330 B gsims=120 B 364 B   
============== ===================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.215     0.0       1     
total count_ruptures           0.007     3.320     1     
managing sources               0.004     0.0       1     
store source_info              0.004     0.0       1     
splitting sources              3.493E-04 0.0       1     
reading site collection        2.985E-04 0.0       1     
unpickling count_ruptures      4.840E-05 0.0       1     
saving probability maps        3.052E-05 0.0       1     
aggregate curves               2.217E-05 0.0       1     
============================== ========= ========= ======