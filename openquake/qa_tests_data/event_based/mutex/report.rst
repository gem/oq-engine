Event Based QA Test, Case 1
===========================

============== ===================
checksum32     3,529,984,501      
date           2018-10-05T03:04:50
engine_version 3.3.0-git48e9a474fd
============== ===================

num_sites = 1, num_levels = 46

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         2000              
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1066              
=============================== ==================

Input files
-----------
======================= ======================================
Name                    File                                  
======================= ======================================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_              
job_ini                 `job.ini <job.ini>`_                  
source                  `source_model.xml <source_model.xml>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_              
======================= ======================================

Slowest sources
---------------
====== ========= ==== ====== ====== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1  gidx2  num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ====== ====== ============ ========= ========== ========= ========= ======
0      case_01   N    0      1,207  1            0.0       1.860E-05  0.0       1         0.0   
0      case_02   N    1,207  3,599  1            0.0       7.629E-06  0.0       1         0.0   
0      case_03   N    3,599  5,132  1            0.0       5.007E-06  0.0       1         0.0   
0      case_04   N    5,132  8,525  1            0.0       4.292E-06  0.0       1         0.0   
0      case_05   N    8,525  12,124 1            0.0       4.530E-06  0.0       1         0.0   
0      case_06   N    12,124 17,050 1            0.0       4.292E-06  0.0       1         0.0   
0      case_07   N    17,050 21,872 1            0.0       4.292E-06  0.0       1         0.0   
0      case_08   N    21,872 28,021 1            0.0       4.292E-06  0.0       1         0.0   
0      case_09   N    28,021 29,255 1            0.0       4.768E-06  0.0       1         0.0   
0      case_10   N    29,255 32,080 1            0.0       4.053E-06  0.0       1         0.0   
====== ========= ==== ====== ====== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.0       10    
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.19370 NaN    0.19370 0.19370 1      
split_filter       0.00502 NaN    0.00502 0.00502 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ========================================================================= =========
task               sent                                                                      received 
read_source_models monitor=0 B fnames=0 B converter=0 B                                      755.87 KB
split_filter       srcs=755.85 KB monitor=428 B srcfilter=220 B sample_factor=21 B seed=14 B 756.33 KB
================== ========================================================================= =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.19370  1.98828   1     
updating source_info     0.01706  1.98828   1     
total split_filter       0.00502  1.98828   1     
======================== ======== ========= ======