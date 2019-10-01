Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     1,250,935,976      
date           2019-10-01T06:08:14
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 100, num_levels = 1, num_rlzs = ?

Parameters
----------
=============================== =================
calculation_mode                'event_based'    
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              30.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            5.0              
complex_fault_mesh_spacing      5.0              
width_of_mfd_bin                0.1              
area_source_discretization      18.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     42               
master_seed                     0                
ses_seed                        23               
=============================== =================

Input files
-----------
======================= ==============================================================================
Name                    File                                                                          
======================= ==============================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                                          
sites                   `sites.csv <sites.csv>`_                                                      
source_model_logic_tree `combined_logic-tree-source-model.xml <combined_logic-tree-source-model.xml>`_
======================= ==============================================================================

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       13    
P    0.0       51    
S    0.0       4     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.05802 0.06167 0.01128 0.12792 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ======================================== =========
task         sent                                     received 
SourceReader apply_unc=6 KB ltmodel=620 B fname=353 B 106.54 KB
============ ======================================== =========

Slowest operations
------------------
====================== ======== ========= ======
calc_23102             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.17407  0.77344   3     
composite source model 0.14608  0.29297   1     
====================== ======== ========= ======