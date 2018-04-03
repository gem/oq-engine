Classical PSHA-Based Hazard
===========================

============== ===================
checksum32     343,519,400        
date           2018-03-26T15:54:56
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 1, num_levels = 8

Parameters
----------
=============================== ==================
calculation_mode                'classical_damage'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
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
b1        1.000  simple(2)       2/2             
========= ====== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================== ========= ========== ==========
grp_id gsims                              distances siteparams ruptparams
====== ================================== ========= ========== ==========
0      AkkarBommer2010() SadighEtAl1997() rjb rrup  vs30       mag rake  
====== ================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): [1]
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
#assets         1       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
Wood     1.000 NaN    1   1   1         1         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
========= ================= ============ ========= ========== ========= =========
source_id source_class      num_ruptures calc_time split_time num_sites num_split
========= ================= ============ ========= ========== ========= =========
1         SimpleFaultSource 1,694        0.093     2.832E-04  15        15       
========= ================= ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.093     1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.009 0.002  0.004 0.010 14       
================== ===== ====== ===== ===== =========

Informational data
------------------
============== ============================================================================== ========
task           sent                                                                           received
count_ruptures sources=14.75 KB srcfilter=9.87 KB param=6.26 KB monitor=4.51 KB gsims=2.86 KB 4.98 KB 
============== ============================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total count_ruptures           0.123     3.445     14    
managing sources               0.029     0.0       1     
reading composite source model 0.017     0.0       1     
reading exposure               0.004     0.0       1     
store source_info              0.004     0.0       1     
splitting sources              7.141E-04 0.0       1     
unpickling count_ruptures      5.157E-04 0.0       14    
aggregate curves               2.346E-04 0.0       14    
reading site collection        5.198E-05 0.0       1     
saving probability maps        2.980E-05 0.0       1     
============================== ========= ========= ======