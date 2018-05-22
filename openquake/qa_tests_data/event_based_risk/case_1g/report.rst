event based risk with PMF
=========================

============== ===================
checksum32     3,942,037,274      
date           2018-05-15T04:13:03
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 1, num_levels = 8

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1000.0            
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

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
source_model.xml 0      Active Shallow Crust 482          482         
================ ====== ==================== ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
1 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 60 tasks = 480 B

Exposure model
--------------
=============== ========
#assets         1       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
1         SimpleFaultSource 2            0.31780   0.0        15        15        48    
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.31780   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
prefilter          0.00756 0.00192 0.00389 0.01162 15       
compute_ruptures   0.06228 0.02409 0.03038 0.10236 6        
================== ======= ======= ======= ======= =========

Informational data
------------------
================ =========================================================================== ========
task             sent                                                                        received
prefilter        srcs=19.36 KB monitor=4.73 KB srcfilter=3.35 KB                             19.96 KB
compute_ruptures sources=10.76 KB src_filter=4.2 KB param=3.6 KB monitor=1.93 KB gsims=786 B 41.79 KB
================ =========================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.37368   4.75781   6     
managing sources               0.18133   0.0       1     
total prefilter                0.11335   5.07031   15    
making contexts                0.08640   0.0       31    
saving ruptures                0.01425   0.0       6     
reading composite source model 0.00573   0.0       1     
store source_info              0.00420   0.0       1     
reading site collection        0.00220   0.0       1     
unpickling compute_ruptures    0.00182   0.0       6     
setting event years            0.00148   0.0       1     
unpickling prefilter           0.00134   0.0       15    
reading exposure               8.886E-04 0.0       1     
splitting sources              6.030E-04 0.0       1     
============================== ========= ========= ======