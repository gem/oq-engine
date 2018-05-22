Calculation of the ground motion fields for a scenario
======================================================

============== ===================
checksum32     3,734,678,775      
date           2018-05-15T04:12:42
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 11, num_levels = 1

Parameters
----------
=============================== ==================
calculation_mode                'scenario'        
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            15.0              
complex_fault_mesh_spacing      15.0              
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     3                 
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
============= ==========================================
Name          File                                      
============= ==========================================
exposure      `exposure_model.xml <exposure_model.xml>`_
job_ini       `job_haz.ini <job_haz.ini>`_              
rupture_model `fault_rupture.xml <fault_rupture.xml>`_  
============= ==========================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 trivial(1)      1/1             
========= ======= =============== ================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): [0]>

Exposure model
--------------
=============== ========
#assets         11      
#taxonomies     4       
deductibile     relative
insurance_limit relative
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
W        1.00000 0.0    1   1   2         2         
A        1.00000 0.0    1   1   5         5         
DS       1.00000 0.0    1   1   2         2         
UFB      1.00000 0.0    1   1   2         2         
*ALL*    1.00000 0.0    1   1   11        11        
======== ======= ====== === === ========= ==========

Slowest operations
------------------
======================= ======== ========= ======
operation               time_sec memory_mb counts
======================= ======== ========= ======
reading site collection 0.00364  0.0       1     
reading exposure        0.00180  0.0       1     
======================= ======== ========= ======