Classical PSHA-Based Hazard
===========================

============== ===================
checksum32     3,640,380,985      
date           2018-03-26T15:54:57
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 7, num_levels = 8

Parameters
----------
=============================== ==================
calculation_mode                'classical_damage'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job_haz.ini <job_haz.ini>`_                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_fragility    `fragility_model.xml <fragility_model.xml>`_                
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
source_model.xml 0      Active Shallow Crust 1,694        1,694       
================ ====== ==================== ============ ============

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
Wood     1.000 0.0    1   1   3         3         
Concrete 1.000 0.0    1   1   2         2         
Steel    1.000 0.0    1   1   2         2         
*ALL*    1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
========= ================= ============ ========= ========== ========= =========
source_id source_class      num_ruptures calc_time split_time num_sites num_split
========= ================= ============ ========= ========== ========= =========
1         SimpleFaultSource 1,694        0.085     2.453E-04  105       15       
========= ================= ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.085     1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.008 0.004  0.004 0.019 13       
================== ===== ====== ===== ===== =========

Informational data
------------------
============== =============================================================================== ========
task           sent                                                                            received
count_ruptures sources=13.88 KB srcfilter=13.32 KB param=5.81 KB monitor=4.19 KB gsims=1.52 KB 4.62 KB 
============== =============================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           0.108     3.453     13    
managing sources               0.027     0.0       1     
reading composite source model 0.014     0.0       1     
reading exposure               0.005     0.0       1     
store source_info              0.004     0.0       1     
splitting sources              6.251E-04 0.0       1     
unpickling count_ruptures      5.391E-04 0.0       13    
aggregate curves               2.332E-04 0.0       13    
reading site collection        5.174E-05 0.0       1     
saving probability maps        3.052E-05 0.0       1     
============================== ========= ========= ======