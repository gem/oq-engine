Classical Hazard QA Test, Case 7
================================

============== ===================
checksum32     359,954,679        
date           2018-03-26T15:56:11
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
rupture_mesh_spacing            0.1               
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
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        0.700  trivial(1)      1/1             
b2        0.300  trivial(1)      0/0             
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
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 140          140         
================== ====== ==================== ============ ============

Slowest sources
---------------
========= ================== ============ ========= ========== ========= =========
source_id source_class       num_ruptures calc_time split_time num_sites num_split
========= ================== ============ ========= ========== ========= =========
2         ComplexFaultSource 49           0.005     6.437E-06  1         1        
1         SimpleFaultSource  91           0.005     5.245E-06  1         1        
========= ================== ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
ComplexFaultSource 0.005     1     
SimpleFaultSource  0.005     1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_ruptures     0.006 5.088E-04 0.006 0.006 2        
================== ===== ========= ===== ===== =========

Informational data
------------------
============== ======================================================================= ========
task           sent                                                                    received
count_ruptures sources=2.22 KB srcfilter=1.41 KB param=836 B monitor=660 B gsims=240 B 728 B   
============== ======================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.285     0.0       1     
total count_ruptures           0.012     3.754     2     
managing sources               0.007     0.0       1     
store source_info              0.004     0.0       1     
splitting sources              4.201E-04 0.0       1     
reading site collection        3.588E-04 0.0       1     
unpickling count_ruptures      7.987E-05 0.0       2     
aggregate curves               3.910E-05 0.0       2     
saving probability maps        2.956E-05 0.0       1     
============================== ========= ========= ======