Scenario QA Test 3
==================

gem-tstation:/home/michele/ssd/calc_120.hdf5 updated Wed Apr 27 10:57:14 2016

num_sites = 4, sitecol = 877 B

Parameters
----------
============================ ===================
calculation_mode             'scenario_risk'    
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 300}   
investigation_time           None               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         10.0               
complex_fault_mesh_spacing   10.0               
width_of_mfd_bin             None               
area_source_discretization   None               
random_seed                  3                  
master_seed                  0                  
avg_losses                   False              
oqlite_version               '0.13.0-gitcbbc4a8'
============================ ===================

Input files
-----------
======================== ====================================================
Name                     File                                                
======================== ====================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_          
job_ini                  `job.ini <job.ini>`_                                
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_            
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_
======================== ====================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['ChiouYoungs2008']>

Exposure model
--------------
=========== =
#assets     4
#taxonomies 3
=========== =

======== =======
Taxonomy #Assets
======== =======
RC       1      
RM       1      
W        2      
======== =======

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
computing gmfs          0.061     0.0       1     
total scenario_risk     0.008     0.004     4     
filtering sites         0.006     0.0       1     
computing risk          0.006     0.0       4     
reading exposure        0.003     0.0       1     
saving gmfs             0.001     0.0       1     
building epsilons       5.672E-04 0.0       1     
building riskinputs     5.090E-04 0.0       1     
building hazard         9.418E-05 0.0       4     
reading site collection 6.914E-06 0.0       1     
======================= ========= ========= ======