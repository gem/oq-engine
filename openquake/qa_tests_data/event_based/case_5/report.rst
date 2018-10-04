Germany_SHARE Combined Model event_based
========================================

============== ===================
checksum32     3,726,424,986      
date           2018-10-04T15:36:35
engine_version 3.3.0-gitf22d3f2c70
============== ===================

num_sites = 100, num_levels = 1

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
source                  `as_model.xml <as_model.xml>`_                                                
source                  `fs_bg_source_model.xml <fs_bg_source_model.xml>`_                            
source                  `ss_model_final_250km_Buffer.xml <ss_model_final_250km_Buffer.xml>`_          
source_model_logic_tree `combined_logic-tree-source-model.xml <combined_logic-tree-source-model.xml>`_
======================= ==============================================================================

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1         A    0     4     7            0.0       0.00175    0.0       1         0.0   
0      2         A    4     8     7            0.0       0.00142    0.0       1         0.0   
1      1339      A    0     10    168          0.0       0.04027    0.0       12        0.0   
1      19        S    10    73    349          0.0       0.00199    0.0       12        0.0   
1      20        S    73    92    31           0.0       5.536E-04  0.0       6         0.0   
1      21        S    92    101   7            0.0       2.222E-04  0.0       4         0.0   
1      22        S    101   115   34           0.0       4.048E-04  0.0       6         0.0   
1      246       A    115   121   156          0.0       0.05295    0.0       13        0.0   
1      247       A    121   127   156          0.0       0.05004    0.0       13        0.0   
1      248       A    127   138   384          0.0       0.06889    0.0       7         0.0   
1      249       A    138   149   384          0.0       0.06931    0.0       7         0.0   
1      250       A    149   160   384          0.0       0.06946    0.0       7         0.0   
1      257       A    160   173   96           0.0       0.02156    0.0       8         0.0   
1      258       A    173   186   96           0.0       0.02094    0.0       8         0.0   
1      259       A    186   199   96           0.0       0.02087    0.0       8         0.0   
1      263       A    199   211   1,022        0.0       0.17814    0.0       9         0.0   
1      264       A    211   223   1,022        0.0       0.16905    0.0       9         0.0   
2      101622    P    0     1     39           0.0       0.0        0.0       0         0.0   
2      101623    P    1     2     36           0.0       0.0        0.0       0         0.0   
3      323839    P    2     3     6            0.0       0.0        0.0       0         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       13    
P    0.0       51    
S    0.0       4     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.04886 0.06068 0.00854 0.11865 3      
split_filter       0.18639 NaN     0.18639 0.18639 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================================================== ========
task               sent                                                                     received
read_source_models monitor=993 B converter=957 B fnames=608 B                               45.33 KB
split_filter       srcs=67.18 KB monitor=343 B srcfilter=220 B sample_factor=21 B seed=14 B 77.7 KB 
================== ======================================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
updating source_info     0.21108  0.0       1     
total split_filter       0.18639  0.50000   1     
total read_source_models 0.14659  0.39844   3     
======================== ======== ========= ======