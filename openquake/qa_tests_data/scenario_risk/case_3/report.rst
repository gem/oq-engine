Scenario QA Test 3
==================

gem-tstation:/home/michele/ssd/calc_16121.hdf5 updated Wed May 11 14:31:08 2016

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
oqlite_version               '0.13.0-git7639915'
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
  0,ChiouYoungs2008(): ['ChiouYoungs2008()']>

Exposure model
--------------
=========== =
#assets     4
#taxonomies 3
=========== =

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
RC       1.000 NaN    1   1   1         1         
RM       1.000 NaN    1   1   1         1         
W        1.000 0.0    1   1   2         2         
*ALL*    1.000 0.0    1   1   4         4         
======== ===== ====== === === ========= ==========

Information about the tasks
---------------------------
======================= ===== ========= ========= ===== =========
measurement             mean  stddev    min       max   num_tasks
scenario_risk.time_sec  0.002 9.839E-04 5.679E-04 0.003 4        
scenario_risk.memory_mb 0.005 0.005     0.0       0.012 4        
======================= ===== ========= ========= ===== =========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
computing gmfs          0.069     0.0       1     
total scenario_risk     0.008     0.012     4     
filtering sites         0.007     0.0       1     
computing riskmodel     0.006     0.0       4     
reading exposure        0.004     0.0       1     
saving gmfs             0.002     0.0       1     
building epsilons       6.192E-04 0.0       1     
building riskinputs     5.169E-04 0.0       1     
building hazard         1.140E-04 0.0       4     
reading site collection 5.960E-06 0.0       1     
======================= ========= ========= ======