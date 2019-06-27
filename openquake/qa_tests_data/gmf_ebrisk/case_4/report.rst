event based two source models
=============================

============== ===================
checksum32     1,852,256,743      
date           2019-06-24T15:33:21
engine_version 3.6.0-git4b6205639c
============== ===================

num_sites = 1, num_levels = 11, num_rlzs = ?

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         2                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     24                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                              
job_ini                  `job_haz.ini <job_haz.ini>`_                                              
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight checksum     
====== ========= ==== ===== ===== ============ ========= ========= ====== =============
3      2         X    6     402   1            0.0       0.0       0.0    2,506,021,815
2      1         S    4     6     482          0.0       0.0       0.0    2,786,737,502
1      2         S    2     4     4            0.0       0.0       0.0    3,056,286,023
0      1         S    0     2     482          0.0       0.0       0.0    2,786,737,502
====== ========= ==== ===== ===== ============ ========= ========= ====== =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.0       3     
X    0.0       1     
==== ========= ======

Duplicated sources
------------------
Found 2 source(s) with the same ID and 1 true duplicate(s): ['1']
Here is a fake duplicate: 2

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.01653 0.00782 0.01100 0.02206 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================ ========
task               sent                         received
read_source_models converter=626 B fnames=218 B 13.93 KB
================== ============================ ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.03306   0.23828   2     
reading exposure         5.176E-04 0.0       1     
======================== ========= ========= ======