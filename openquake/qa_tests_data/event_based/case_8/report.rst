Event Based from NonParametric source
=====================================

============== ====================
checksum32     3_420_346_662       
date           2020-11-02T08:41:27 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 3, num_levels = 7, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 500.0), (10.0, 500.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         2                                         
truncation_level                3.0                                       
rupture_mesh_spacing            5.0                                       
complex_fault_mesh_spacing      5.0                                       
width_of_mfd_bin                0.3                                       
area_source_discretization      20.0                                      
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
====== ================= ====
grp_id gsim              rlzs
====== ================= ====
0      [ChiouYoungs2008] [0] 
====== ================= ====

Required parameters per tectonic region type
--------------------------------------------
===== =================== =========== ======================= =================
et_id gsims               distances   siteparams              ruptparams       
===== =================== =========== ======================= =================
0     '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
===== =================== =========== ======================= =================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         N    5.996E-04 3         4           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    5.996E-04
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       1      0.00102 nan    0.00102 0.00102
read_source_model  1      0.18251 nan    0.18251 0.18251
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      14.84 KB
preclassical           239 B   
================= ==== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46569, maxmem=0.5 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.29654  0.0       1     
composite source model    0.29137  0.0       1     
total read_source_model   0.18251  0.0       1     
total preclassical        0.00102  0.0       1     
========================= ======== ========= ======