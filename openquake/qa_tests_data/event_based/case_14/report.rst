Hazard South Africa
===================

============== ===================
checksum32     3,623,115,332      
date           2018-10-05T03:04:49
engine_version 3.3.0-git48e9a474fd
============== ===================

num_sites = 18, num_levels = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    3                 
maximum_distance                {'default': 100.0}
investigation_time              100.0             
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        23                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_                                    
job_ini                 `job.ini <job.ini>`_                                        
site_model              `Site_model_South_Africa.xml <Site_model_South_Africa.xml>`_
source                  `nwest_18.xml <nwest_18.xml>`_                              
source                  `snam_19.xml <snam_19.xml>`_                                
source                  `wbots_20.xml <wbots_20.xml>`_                              
source                  `welkom_21.xml <welkom_21.xml>`_                            
source                  `wrand_22.xml <wrand_22.xml>`_                              
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_                                    
======================= ============================================================

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      18        A    0     7     480          0.0       0.98719    0.0       47        0.0   
1      19        A    0     7     12,690       0.0       0.0        0.0       0         0.0   
2      20        A    0     13    23,199       0.0       0.70856    0.0       4         0.0   
3      21        A    0     11    84           0.0       0.13260    0.0       11        0.0   
4      22        A    0     13    8            0.0       0.00566    0.0       2         0.0   
5      18        A    0     7     320          0.0       0.88629    0.0       47        0.0   
6      19        A    0     7     6,345        0.0       0.0        0.0       0         0.0   
7      20        A    0     13    12,654       0.0       0.47742    0.0       3         0.0   
8      21        A    0     11    168          0.0       0.13542    0.0       11        0.0   
9      22        A    0     13    52           0.0       0.00419    0.0       2         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       10    
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.05479 0.06500 0.00539 0.15788 5      
split_filter       0.13062 0.10550 0.01908 0.25868 5      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================================================== ========
task               sent                                                                           received
read_source_models monitor=1.62 KB converter=1.56 KB fnames=920 B                                 12.89 KB
split_filter       srcs=236.67 KB monitor=2.01 KB srcfilter=1.29 KB sample_factor=126 B seed=84 B 43.93 KB
================== ============================================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.65309  0.76172   5     
total read_source_models 0.27396  0.0       5     
updating source_info     0.26677  0.0       1     
======================== ======== ========= ======