event based risk
================

============== ===================
checksum32     1,223,742,661      
date           2018-09-05T10:04:22
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 7, num_levels = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              10000.0           
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      None              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     24                
master_seed                     42                
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
occupants_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
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
source_model.xml 0      Active Shallow Crust 482          482         
================ ====== ==================== ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 60 tasks = 3.28 KB

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
========= ================= ============ ========= ========== ========= ========= ======
source_id source_class      num_ruptures calc_time split_time num_sites num_split events
========= ================= ============ ========= ========== ========= ========= ======
1         SimpleFaultSource 482          0.75811   1.719E-04  7.00000   15        385   
========= ================= ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================= ========= ======
source_class      calc_time counts
================= ========= ======
SimpleFaultSource 0.75811   1     
================= ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ======= ======= =========
operation-duration   mean    stddev    min     max     num_tasks
pickle_source_models 0.00439 NaN       0.00439 0.00439 1        
preprocess           0.06829 0.01654   0.03876 0.10357 14       
compute_gmfs         0.00759 3.298E-05 0.00755 0.00762 3        
==================== ======= ========= ======= ======= =========

Data transfer
-------------
==================== =============================================================================================== =========
task                 sent                                                                                            received 
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                                            165 B    
preprocess           srcs=18.55 KB monitor=4.88 KB param=4.05 KB srcfilter=3.46 KB                                   283.99 KB
compute_gmfs         sources_or_ruptures=272.84 KB param=8.69 KB monitor=1.01 KB rlzs_by_gsim=903 B src_filter=660 B 263.23 KB
==================== =============================================================================================== =========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
total preprocess           0.95600   9.25000   14    
making contexts            0.55678   0.0       259   
saving ruptures            0.12226   0.0       15    
total compute_gmfs         0.02278   5.34375   3     
managing sources           0.01598   0.0       1     
building ruptures          0.01208   5.26953   3     
GmfGetter.init             0.00761   0.0       3     
store source_info          0.00484   0.0       1     
total pickle_source_models 0.00454   0.0       3     
setting event years        0.00192   0.0       1     
reading exposure           9.704E-04 0.0       1     
aggregating hcurves        6.711E-04 0.0       3     
splitting sources          4.246E-04 0.0       1     
========================== ========= ========= ======