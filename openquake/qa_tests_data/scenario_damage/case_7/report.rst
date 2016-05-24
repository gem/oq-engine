scenario hazard
===============

gem-tstation:/home/michele/ssd/calc_16345.hdf5 updated Wed May 18 18:18:23 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===================
calculation_mode             'scenario'         
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           None               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             None               
area_source_discretization   None               
random_seed                  42                 
master_seed                  0                  
oqlite_version               '0.13.0-git034c0a0'
============================ ===================

Input files
-----------
============= ==========================================
Name          File                                      
============= ==========================================
exposure      `exposure_model.xml <exposure_model.xml>`_
job_ini       `job_h.ini <job_h.ini>`_                  
rupture_model `rupture_model.xml <rupture_model.xml>`_  
============= ==========================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): ['<0,b_1,b1,w=1.0>']>

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
tax1     1.000 NaN    1   1   1         1         
======== ===== ====== === === ========= ==========

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
filtering sites         0.006     0.0       1     
reading exposure        0.002     0.0       1     
computing gmfs          0.001     0.0       1     
reading site collection 6.199E-06 0.0       1     
======================= ========= ========= ======