Hazard South Africa
===================

============== ===================
checksum32     3,741,932,100      
date           2018-12-13T12:57:40
engine_version 3.3.0-git68d7d11268
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
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_                                    
======================= ============================================================

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      18        A    0     7     480          0.0       1.13316    0.0       47        0.0   
1      19        A    0     7     12,690       0.0       0.0        0.0       0         0.0   
2      20        A    0     13    23,199       0.0       0.72961    0.0       4         0.0   
3      21        A    0     11    84           0.0       0.06909    0.0       11        0.0   
4      22        A    0     13    8            0.0       0.00312    0.0       2         0.0   
5      18        A    0     7     320          0.0       1.67821    0.0       47        0.0   
6      19        A    0     7     6,345        0.0       0.0        0.0       0         0.0   
7      20        A    0     13    12,654       0.0       0.51623    0.0       3         0.0   
8      21        A    0     11    168          0.0       0.12750    0.0       11        0.0   
9      22        A    0     13    52           0.0       0.00302    0.0       2         0.0   
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
read_source_models 0.06281 0.06699 0.00467 0.17464 10     
split_filter       0.14989 0.11662 0.02002 0.27268 5      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ========================================= ========
task               sent                                      received
read_source_models converter=3.79 KB fnames=1.06 KB          25.68 KB
split_filter       srcs=17.45 KB srcfilter=1.48 KB seed=84 B 46.52 KB
================== ========================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.74946  0.99219   5     
total read_source_models 0.62806  0.0       10    
======================== ======== ========= ======