Scenario Risk for Nepal with 20 assets
======================================

gem-tstation:/home/michele/ssd/calc_22626.hdf5 updated Tue May 31 15:39:17 2016

num_sites = 20, sitecol = 1.58 KB

Parameters
----------
============================ ==================
calculation_mode             'scenario_risk'   
number_of_logic_tree_samples 0                 
maximum_distance             {'default': 500}  
investigation_time           None              
ses_per_logic_tree_path      1                 
truncation_level             3.0               
rupture_mesh_spacing         15.0              
complex_fault_mesh_spacing   15.0              
width_of_mfd_bin             None              
area_source_discretization   None              
random_seed                  42                
master_seed                  0                 
avg_losses                   False             
engine_version               '2.0.0-git4fb4450'
============================ ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                
job_ini                  `job.ini <job.ini>`_                                                      
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_                                  
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b_1~b1,w=1.0>']>

Exposure model
--------------
=========== ==
#assets     20
#taxonomies 4 
=========== ==

========================== ===== ====== === === ========= ==========
taxonomy                   mean  stddev min max num_sites num_assets
Adobe                      1.000 0.0    1   1   3         3         
Stone-Masonry              1.000 0.0    1   1   4         4         
Unreinforced-Brick-Masonry 1.000 0.0    1   1   5         5         
Wood                       1.000 0.0    1   1   8         8         
*ALL*                      1.000 0.0    1   1   20        20        
========================== ===== ====== === === ========= ==========

Information about the tasks
---------------------------
======================= ===== ========= ========= ===== =========
measurement             mean  stddev    min       max   num_tasks
scenario_risk.time_sec  0.001 2.392E-04 8.042E-04 0.001 20       
scenario_risk.memory_mb 0.0   0.0       0.0       0.0   20       
======================= ===== ========= ========= ===== =========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
total scenario_risk     0.023     0.0       20    
computing riskmodel     0.012     0.0       20    
reading exposure        0.011     0.0       1     
filtering sites         0.004     0.0       1     
computing gmfs          0.003     0.0       1     
building hazard         0.002     0.0       20    
saving gmfs             0.001     0.0       1     
building riskinputs     9.220E-04 0.0       1     
building epsilons       2.561E-04 0.0       1     
reading site collection 7.153E-06 0.0       1     
======================= ========= ========= ======