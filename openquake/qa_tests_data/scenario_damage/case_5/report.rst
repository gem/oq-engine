Calculation of the ground motion fields for a scenario
======================================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_48390.hdf5 Wed Sep  7 16:04:05 2016
engine_version                                 2.1.0-gitfaa2965        
hazardlib_version                              0.21.0-git89bccaf       
============================================== ========================

num_sites = 7, sitecol = 825 B

Parameters
----------
============================ =================
calculation_mode             'scenario'       
number_of_logic_tree_samples 0                
maximum_distance             {u'default': 200}
investigation_time           None             
ses_per_logic_tree_path      1                
truncation_level             3.0              
rupture_mesh_spacing         15.0             
complex_fault_mesh_spacing   15.0             
width_of_mfd_bin             None             
area_source_discretization   None             
random_seed                  3                
master_seed                  0                
============================ =================

Input files
-----------
============= ==========================================
Name          File                                      
============= ==========================================
exposure      `exposure_model.xml <exposure_model.xml>`_
job_ini       `job_haz.ini <job_haz.ini>`_              
rupture_model `fault_rupture.xml <fault_rupture.xml>`_  
============= ==========================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b_1~b1,w=1.0>']>

Exposure model
--------------
=============== ========
#assets         11      
#taxonomies     4       
deductibile     relative
insurance_limit relative
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
A        1.000 0.0    1   1   5         5         
DS       1.000 0.0    1   1   2         2         
UFB      1.000 0.0    1   1   2         2         
W        1.000 0.0    1   1   2         2         
*ALL*    1.000 0.0    1   1   11        11        
======== ===== ====== === === ========= ==========

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
reading exposure        0.005     0.0       1     
filtering sites         0.003     0.0       1     
reading site collection 8.106E-06 0.0       1     
======================= ========= ========= ======