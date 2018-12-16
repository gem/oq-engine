event based hazard
==================

============== ===================
checksum32     485,638,434        
date           2018-12-13T12:57:45
engine_version 3.3.0-git68d7d11268
============== ===================

num_sites = 1, num_levels = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         200               
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
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job_h.ini <job_h.ini>`_                                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Exposure model
--------------
=============== ========
#assets         1       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
Wood     1.00000 NaN    1   1   1         1         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1         S    0     2     482          0.0       0.00605    0.0       15        0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.0       1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.00366 NaN    0.00366 0.00366 1      
split_filter       0.03240 NaN    0.03240 0.03240 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ===================================== ========
task               sent                                  received
read_source_models converter=388 B fnames=114 B          1.46 KB 
split_filter       srcs=1.1 KB srcfilter=253 B seed=14 B 8.22 KB 
================== ===================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total split_filter       0.03240   0.31250   1     
total read_source_models 0.00366   0.0       1     
reading exposure         5.019E-04 0.0       1     
======================== ========= ========= ======