Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     1,250,935,976      
date           2019-05-10T05:07:26
engine_version 3.5.0-gitbaeb4c1e35
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
====== ========= ==== ===== ===== ============ ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========= ==== ===== ===== ============ ========= ========= ======
4      330080    P    281   282   12           0.0       0.0       0.0   
4      330079    P    280   281   12           0.0       0.0       0.0   
4      330078    P    279   280   12           0.0       0.0       0.0   
4      330077    P    278   279   20           0.0       0.0       0.0   
4      330076    P    277   278   18           0.0       0.0       0.0   
4      330075    P    276   277   16           0.0       0.0       0.0   
4      330074    P    275   276   14           0.0       0.0       0.0   
4      330073    P    274   275   14           0.0       0.0       0.0   
4      330072    P    273   274   14           0.0       0.0       0.0   
4      330071    P    272   273   12           0.0       0.0       0.0   
4      330070    P    271   272   12           0.0       0.0       0.0   
4      330069    P    270   271   12           0.0       0.0       0.0   
4      330068    P    269   270   18           0.0       0.0       0.0   
4      330067    P    268   269   16           0.0       0.0       0.0   
4      330066    P    267   268   14           0.0       0.0       0.0   
4      330065    P    266   267   14           0.0       0.0       0.0   
4      330064    P    265   266   14           0.0       0.0       0.0   
4      330063    P    264   265   12           0.0       0.0       0.0   
4      330062    P    263   264   12           0.0       0.0       0.0   
4      330061    P    262   263   18           0.0       0.0       0.0   
====== ========= ==== ===== ===== ============ ========= ========= ======

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
read_source_models 0.05250 0.06932 0.00915 0.13245 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================ ========
task               sent                         received
read_source_models converter=939 B fnames=383 B 47.02 KB
================== ============================ ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.15750  0.26172   3     
======================== ======== ========= ======