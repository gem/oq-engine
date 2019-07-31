Vancouver - 5 branches - 5 Years
================================

============== ===================
checksum32     2,220,417,399      
date           2019-07-30T15:03:49
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 2, num_levels = 1, num_rlzs = ?

Parameters
----------
=============================== ================================
calculation_mode                'event_based'                   
number_of_logic_tree_samples    1                               
maximum_distance                {'default': 200.0}              
investigation_time              10.0                            
ses_per_logic_tree_path         1                               
truncation_level                3.0                             
rupture_mesh_spacing            10.0                            
complex_fault_mesh_spacing      10.0                            
width_of_mfd_bin                0.5                             
area_source_discretization      10.0                            
ground_motion_correlation_model None                            
minimum_intensity               {'SA(0.3)': 0.1, 'default': 0.1}
random_seed                     24                              
master_seed                     0                               
ses_seed                        23                              
=============================== ================================

Input files
-----------
======================= ==============================================
Name                    File                                          
======================= ==============================================
gsim_logic_tree         `gmmLT_analytical.xml <gmmLT_analytical.xml>`_
job_ini                 `job.ini <job.ini>`_                          
site_model              `Vs30_Vancouver.xml <Vs30_Vancouver.xml>`_    
source_model_logic_tree `ssmLT_0.xml <ssmLT_0.xml>`_                  
======================= ==============================================

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ====== =====
source_id grp_id code num_ruptures calc_time num_sites weight speed
========= ====== ==== ============ ========= ========= ====== =====
========= ====== ==== ============ ========= ========= ====== =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       4     
C    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.58201 NaN    0.58201 0.58201 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ============================ ========
task               sent                         received
read_source_models converter=314 B fnames=104 B 10.22 KB
================== ============================ ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15468               time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.58201  0.67578   1     
======================== ======== ========= ======