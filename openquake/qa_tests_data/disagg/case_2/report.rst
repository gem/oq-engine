QA test for disaggregation case_2
=================================

============== ===================
checksum32     3,620,311,746      
date           2019-02-18T08:36:00
engine_version 3.4.0-git9883ae17a5
============== ===================

num_sites = 2, num_levels = 1

Parameters
----------
=============================== =================
calculation_mode                'disaggregation' 
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              1.0              
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            4.0              
complex_fault_mesh_spacing      4.0              
width_of_mfd_bin                0.1              
area_source_discretization      10.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     23               
master_seed                     0                
ses_seed                        42               
=============================== =================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
2      1         S    12    14    1,420        0.0       0.00216    0.0       15        0.0   
1      3         A    8     12    1,815        0.0       2.03432    0.0       121       0.0   
1      1         A    4     8     1,815        0.0       1.44627    0.0       121       0.0   
0      2         A    0     4     1,815        0.0       1.38474    0.0       121       0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       3     
S    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.03342 0.02570 0.01525 0.05159 2      
split_filter       0.04910 0.03370 0.02527 0.07294 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ====================================== ========
task               sent                                   received
read_source_models converter=626 B fnames=210 B           5.41 KB 
split_filter       srcs=3.35 KB srcfilter=253 B seed=14 B 86.17 KB
================== ====================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.09820  2.28125   2     
total read_source_models 0.06683  0.18750   2     
======================== ======== ========= ======