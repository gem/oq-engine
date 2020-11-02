Spinning with maximum_distance=60 km
====================================

============== ====================
checksum32     2_241_407_815       
date           2020-11-02T09:36:54 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 82, num_levels = 20, num_rlzs = 1

Parameters
----------
=============================== ======================================
calculation_mode                'preclassical'                        
number_of_logic_tree_samples    0                                     
maximum_distance                {'default': [(1.0, 200), (10.0, 200)]}
investigation_time              1.0                                   
ses_per_logic_tree_path         1                                     
truncation_level                3.0                                   
rupture_mesh_spacing            5.0                                   
complex_fault_mesh_spacing      10.0                                  
width_of_mfd_bin                0.1                                   
area_source_discretization      150.0                                 
pointsource_distance            {'default': [(1.0, -1), (10.0, -1)]}  
ground_motion_correlation_model None                                  
minimum_intensity               {}                                    
random_seed                     23                                    
master_seed                     0                                     
ses_seed                        42                                    
=============================== ======================================

Input files
-----------
======================= ==============================
Name                    File                          
======================= ==============================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_      
job_ini                 `job.ini <job.ini>`_          
sites                   `sites_RG.csv <sites_RG.csv>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_      
======================= ==============================

Composite source model
----------------------
====== ====================== ====
grp_id gsim                   rlzs
====== ====================== ====
0      '[YuEtAl2013MwStable]' [0] 
====== ====================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ====================== ============ ========== ==========
et_id gsims                  distances    siteparams ruptparams
===== ====================== ============ ========== ==========
0     '[YuEtAl2013MwStable]' azimuth repi            mag       
===== ====================== ============ ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
156       A    1.285E-04 82        780         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    1.285E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      5.598E-04 nan    5.598E-04 5.598E-04
read_source_model  1      0.00423   nan    0.00423   0.00423  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      2.26 KB 
preclassical           241 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47331, maxmem=0.3 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.07977   0.0       1     
composite source model    0.07417   0.0       1     
total read_source_model   0.00423   0.0       1     
total preclassical        5.598E-04 0.0       1     
========================= ========= ========= ======