Classical Hazard QA Test, Case 9
================================

============== ===================
checksum32     1,375,199,152      
date           2018-03-26T15:55:48
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 1, num_levels = 4

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
complex_fault_mesh_spacing      0.01              
width_of_mfd_bin                0.001             
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
b1_b2     0.500  trivial(1)      1/1             
b1_b3     0.500  trivial(1)      1/1             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       mag rake  
1      SadighEtAl1997() rrup      vs30       mag rake  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,SadighEtAl1997(): [0]
  1,SadighEtAl1997(): [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3,000        3,000       
source_model.xml 1      Active Shallow Crust 3,500        3,000       
================ ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 6,500
#tot_ruptures 6,000
#tot_weight   650  
============= =====

Slowest sources
---------------
========= ============ ============ ========= ========== ========= =========
source_id source_class num_ruptures calc_time split_time num_sites num_split
========= ============ ============ ========= ========== ========= =========
1         PointSource  3,500        0.002     2.623E-06  2         2        
========= ============ ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.002     1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.003 0.001  0.002 0.004 2        
================== ===== ====== ===== ===== =========

Informational data
------------------
============== ======================================================================= ========
task           sent                                                                    received
count_ruptures sources=2.33 KB srcfilter=1.41 KB param=852 B monitor=660 B gsims=240 B 730 B   
============== ======================================================================= ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.032     0.0       1     
managing sources               0.019     0.0       1     
total count_ruptures           0.007     1.648     2     
store source_info              0.005     0.0       1     
splitting sources              5.908E-04 0.0       1     
reading site collection        2.806E-04 0.0       1     
unpickling count_ruptures      1.087E-04 0.0       2     
aggregate curves               5.341E-05 0.0       2     
saving probability maps        3.862E-05 0.0       1     
============================== ========= ========= ======