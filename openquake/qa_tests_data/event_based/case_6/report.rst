Event-based PSHA producing hazard curves only
=============================================

============== ===================
checksum32     763,166,759        
date           2018-10-05T03:04:46
engine_version 3.3.0-git48e9a474fd
============== ===================

num_sites = 1, num_levels = 5

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         300               
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        23                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1         A    0     65    2,456        0.0       19         0.0       307       0.0   
1      1         A    0     65    2,456        0.0       17         0.0       307       0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       2     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.05350 0.00395 0.05071 0.05629 2      
split_filter       0.15583 NaN     0.15583 0.15583 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================================================== =========
task               sent                                                                     received 
read_source_models monitor=662 B converter=638 B fnames=368 B                               8.38 KB  
split_filter       srcs=25.79 KB monitor=343 B srcfilter=220 B sample_factor=21 B seed=14 B 179.51 KB
================== ======================================================================== =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
updating source_info     0.20072  0.25781   1     
total split_filter       0.15583  0.25391   1     
total read_source_models 0.10700  0.0       2     
======================== ======== ========= ======