Classical Hazard QA Test, Case 2
================================

============== ===================
checksum32     4_177_765_270      
date           2020-03-13T11:23:10
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.001             
area_source_discretization      None              
pointsource_distance            {'default': 0}    
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
========================= ============================================================
Name                      File                                                        
========================= ============================================================
gsim_logic_tree           `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                   `job.ini <job.ini>`_                                        
reqv:active shallow crust `lookup_asc.hdf5 <lookup_asc.hdf5>`_                        
reqv:stable shallow crust `lookup_sta.hdf5 <lookup_sta.hdf5>`_                        
source_model_logic_tree   `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
========================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.333E-04 3_000        3_000       
1      3.333E-04 3_000        3_000       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      P    3_000        0.01266   3.333E-04 3_000       
2         1      P    3_000        0.01258   3.333E-04 3_000       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.02524  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.01396 1.586E-04 0.01384 0.01407 2      
read_source_model  0.00789 NaN       0.00789 0.00789 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================= ============================================= ========
task              sent                                          received
read_source_model                                               1.96 KB 
preclassical      params=441.04 KB srcs=2.26 KB srcfilter=446 B 740 B   
================= ============================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_67011                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.03170   0.0       1     
total preclassical          0.02791   0.48438   2     
total read_source_model     0.00789   0.0       1     
store source_info           0.00218   0.0       1     
splitting/filtering sources 8.433E-04 0.0       2     
aggregate curves            4.807E-04 0.0       2     
=========================== ========= ========= ======