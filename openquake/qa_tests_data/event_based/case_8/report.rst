Event Based from NonParametric source
=====================================

============== ===================
checksum32     2,117,452,566      
date           2018-01-11T04:30:36
engine_version 2.9.0-git3c583c4   
============== ===================

num_sites = 3, num_imts = 1

Parameters
----------
=============================== =====================
calculation_mode                'event_based_rupture'
number_of_logic_tree_samples    0                    
maximum_distance                {'default': 500.0}   
investigation_time              50.0                 
ses_per_logic_tree_path         1                    
truncation_level                3.0                  
rupture_mesh_spacing            5.0                  
complex_fault_mesh_spacing      5.0                  
width_of_mfd_bin                0.3                  
area_source_discretization      10.0                 
ground_motion_correlation_model None                 
random_seed                     23                   
master_seed                     0                    
=============================== =====================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.047     0.0       1     
reading site collection        5.221E-05 0.0       1     
============================== ========= ========= ======