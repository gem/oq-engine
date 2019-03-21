Vancouver - 5 branches - 5 Years
================================

============== ===================
checksum32     254,214,840        
date           2019-03-19T10:04:21
engine_version 3.5.0-gitad6b69ea66
============== ===================

num_sites = 2, num_levels = 1, num_rlzs = ?

Parameters
----------
=============================== ==================
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
minimum_intensity               {'SA(0.3)': 0.1}  
random_seed                     24                
master_seed                     0                 
ses_seed                        23                
=============================== ==================

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
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
2      JDFN      A    73    84    3,276        0.0       0.0        0.0       1         0.0   
2      AID       A    67    73    51,300       0.0       0.0        0.0       0         0.0   
1      CIS-15    C    17    67    8            0.0       0.0        0.0       1         0.0   
1      AKC       A    9     17    42,525       0.0       0.0        0.0       0         0.0   
0      GTP       A    0     9     5,913        0.0       0.0        0.0       1         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

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
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.61452 NaN     0.61452 0.61452 1      
only_filter        0.00319 0.00118 0.00249 0.00455 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ========================================== ========
task               sent                                       received
read_source_models converter=313 B fnames=111 B               10.26 KB
only_filter        srcs=13.01 KB srcfilter=1.24 KB dummy=70 B 8.05 KB 
================== ========================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.61452  1.87891   1     
total only_filter        0.00957  1.43359   3     
======================== ======== ========= ======