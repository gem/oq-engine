Calculation of the ground motion fields for a scenario
======================================================

gem-tstation:/home/michele/ssd/calc_962.hdf5 updated Thu Apr 28 15:38:30 2016

num_sites = 11, sitecol = 834 B

Parameters
----------
============================ ===================
calculation_mode             'scenario'         
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200}   
investigation_time           None               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         15.0               
complex_fault_mesh_spacing   15.0               
width_of_mfd_bin             None               
area_source_discretization   None               
random_seed                  3                  
master_seed                  0                  
oqlite_version               '0.13.0-git93d6f64'
============================ ===================

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

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['ChiouYoungs2008']>

Exposure model
--------------
=========== ==
#assets     11
#taxonomies 4 
=========== ==

======== =======
Taxonomy #Assets
======== =======
A        5      
DS       2      
UFB      2      
W        2      
======== =======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
reading exposure        0.014     0.0       1     
filtering sites         0.007     0.0       1     
computing gmfs          0.001     0.0       1     
reading site collection 9.060E-06 0.0       1     
======================= ========= ========= ======