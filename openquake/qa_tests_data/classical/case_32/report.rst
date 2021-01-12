Classical PSHA with site class as a site variable
=================================================

============== ====================
checksum32     2_801_080_168       
date           2020-11-02T09:37:29 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 14, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            5.0                                       
complex_fault_mesh_spacing      5.0                                       
width_of_mfd_bin                0.1                                       
area_source_discretization      None                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     23                                        
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ==================== ====
grp_id gsim                 rlzs
====== ==================== ====
0      '[McVerry2006AscSC]' [0] 
====== ==================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ==================== ========= ========== ===================
et_id gsims                distances siteparams ruptparams         
===== ==================== ========= ========== ===================
0     '[McVerry2006AscSC]' rrup      siteclass  hypo_depth mag rake
===== ==================== ========= ========== ===================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
2         S    0.00174   1         310         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.00174  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       1      0.00216 nan    0.00216 0.00216
read_source_model  1      0.00151 nan    0.00151 0.00151
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      1.47 KB 
preclassical           239 B   
================= ==== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47363, maxmem=0.3 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.08790  0.0       1     
composite source model    0.08291  0.0       1     
total preclassical        0.00216  0.0       1     
total read_source_model   0.00151  0.0       1     
========================= ======== ========= ======