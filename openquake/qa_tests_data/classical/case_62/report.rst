Classical Hazard QA Test, Case 2
================================

============== ====================
checksum32     1_768_482_896       
date           2020-11-02T09:37:38 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 4, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                0.0                                       
rupture_mesh_spacing            1.0                                       
complex_fault_mesh_spacing      1.0                                       
width_of_mfd_bin                0.001                                     
area_source_discretization      None                                      
pointsource_distance            {'default': [(1.0, 0), (10.0, 0)]}        
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     1066                                      
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

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
====== ================== ====
grp_id gsim               rlzs
====== ================== ====
0      '[SadighEtAl1997]' [0] 
1      '[SadighEtAl1997]' [0] 
====== ================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ================== ========= ========== ==========
et_id gsims              distances siteparams ruptparams
===== ================== ========= ========== ==========
0     '[SadighEtAl1997]' rrup      vs30       mag rake  
1     '[SadighEtAl1997]' rrup      vs30       mag rake  
===== ================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
2         P    0.00372   1         3_000       
1         P    0.00371   1         3_000       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00743  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       2      0.00419 0%     0.00418 0.00421
read_source_model  1      0.00214 nan    0.00214 0.00214
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= =============================== ========
task              sent                            received
read_source_model                                 1.93 KB 
preclassical      srcfilter=32.28 KB srcs=2.32 KB 478 B   
================= =============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47373, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.13001  0.0       1     
composite source model    0.12500  0.0       1     
total preclassical        0.00839  0.63672   2     
total read_source_model   0.00214  0.0       1     
========================= ======== ========= ======