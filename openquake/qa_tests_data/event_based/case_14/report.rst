Hazard South Africa
===================

============== ===================
checksum32     3,741,932,100      
date           2019-02-03T09:38:28
engine_version 3.4.0-gite8c42e513a
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
9      22        A    89    102   52           0.0       0.0        0.0       1         0.0   
8      21        A    78    89    168          0.0       0.0        0.0       1         0.0   
7      20        A    65    78    12,654       0.0       0.0        0.0       1         0.0   
6      19        A    58    65    6,345        0.0       0.0        0.0       0         0.0   
5      18        A    51    58    320          0.0       0.0        0.0       1         0.0   
4      22        A    38    51    8            0.0       0.0        0.0       1         0.0   
3      21        A    27    38    84           0.0       0.0        0.0       1         0.0   
2      20        A    14    27    23,199       0.0       0.0        0.0       1         0.0   
1      19        A    7     14    12,690       0.0       0.0        0.0       0         0.0   
0      18        A    0     7     480          0.0       0.0        0.0       1         0.0   
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
Found 5 source(s) with the same ID and 0 true duplicate(s)
Here is a fake duplicate: 20

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.04649 0.05471   0.00309 0.13871 10     
only_filter        0.00277 1.105E-04 0.00263 0.00289 5      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ========================================== ========
task               sent                                       received
read_source_models converter=3.06 KB fnames=1.06 KB           26.24 KB
only_filter        srcs=17.58 KB srcfilter=1.48 KB dummy=84 B 14.51 KB
================== ========================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.46488  0.68750   10    
total only_filter        0.01385  1.64844   5     
======================== ======== ========= ======