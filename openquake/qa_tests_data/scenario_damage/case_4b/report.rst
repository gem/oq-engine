scenario hazard
===============

============== ===================
checksum32     2,482,429,138      
date           2018-05-15T04:12:42
engine_version 3.1.0-git0acbc11   
============== ===================

num_sites = 7, num_levels = 1

Parameters
----------
=============================== ==================
calculation_mode                'scenario'        
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
=============== ============================================
Name            File                                        
=============== ============================================
exposure        `exposure_model.xml <exposure_model.xml>`_  
gsim_logic_tree `gsim_logic_tree.xml <gsim_logic_tree.xml>`_
job_ini         `job_haz.ini <job_haz.ini>`_                
rupture_model   `rupture_model.xml <rupture_model.xml>`_    
=============== ============================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 simple(2)       2/2             
========= ======= =============== ================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,BooreAtkinson2008(): [0]
  0,ChiouYoungs2008(): [1]>

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   4         4         
tax2     1.00000 0.0    1   1   2         2         
tax3     1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest operations
------------------
======================= ======== ========= ======
operation               time_sec memory_mb counts
======================= ======== ========= ======
reading site collection 0.00267  0.0       1     
reading exposure        0.00112  0.0       1     
======================= ======== ========= ======