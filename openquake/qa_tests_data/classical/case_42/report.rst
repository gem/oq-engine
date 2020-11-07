SAM int July 2019 A15, 300km
============================

============== ====================
checksum32     937_969_482         
date           2020-11-02T09:37:07 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 15, num_rlzs = 1

Parameters
----------
=============================== ========================================
calculation_mode                'preclassical'                          
number_of_logic_tree_samples    0                                       
maximum_distance                {'default': [(1.0, 1000), (10.0, 1000)]}
investigation_time              1.0                                     
ses_per_logic_tree_path         1                                       
truncation_level                3.0                                     
rupture_mesh_spacing            20.0                                    
complex_fault_mesh_spacing      50.0                                    
width_of_mfd_bin                0.2                                     
area_source_discretization      None                                    
pointsource_distance            None                                    
ground_motion_correlation_model None                                    
minimum_intensity               {}                                      
random_seed                     23                                      
master_seed                     0                                       
ses_seed                        42                                      
=============================== ========================================

Input files
-----------
======================= ================================
Name                    File                            
======================= ================================
gsim_logic_tree         `gmmLT_A15.xml <gmmLT_A15.xml>`_
job_ini                 `job.ini <job.ini>`_            
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_        
======================= ================================

Composite source model
----------------------
====== ================================ ====
grp_id gsim                             rlzs
====== ================================ ====
0      '[AbrahamsonEtAl2015SInterHigh]' [0] 
====== ================================ ====

Required parameters per tectonic region type
--------------------------------------------
===== ================================ ========= ============ ==========
et_id gsims                            distances siteparams   ruptparams
===== ================================ ========= ============ ==========
0     '[AbrahamsonEtAl2015SInterHigh]' rrup      backarc vs30 mag       
===== ================================ ========= ============ ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
int_2     C    0.01593   1         1_755       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.01593  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ======= =======
operation-duration counts mean    stddev min     max    
preclassical       1      0.01637 nan    0.01637 0.01637
read_source_model  1      0.02853 nan    0.02853 0.02853
================== ====== ======= ====== ======= =======

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      34.75 KB
preclassical           243 B   
================= ==== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47348, maxmem=0.9 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.79638  0.0       1     
composite source model    0.79179  0.0       1     
total read_source_model   0.02853  0.0       1     
total preclassical        0.01637  0.0       1     
========================= ======== ========= ======