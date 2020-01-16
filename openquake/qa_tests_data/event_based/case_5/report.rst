Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     1_250_935_976      
date           2020-01-16T05:30:58
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            None             
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      NaN       14           0.0         
1      NaN       4_385        0.0         
2      NaN       75           0.0         
3      NaN       78           0.0         
4      NaN       640          0.0         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.0      
P    0.0      
S    0.0      
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.05887 0.07189 0.00888 0.14125 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ========================================== ========
task         sent                                       received
SourceReader apply_unc=6.1 KB ltmodel=620 B fname=374 B 57.83 KB
============ ========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_43261             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.17661  0.42188   3     
composite source model 0.16748  0.0       1     
====================== ======== ========= ======