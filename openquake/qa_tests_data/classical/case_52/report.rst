late_weights sampling
=====================

============== ====================
checksum32     382_189_057         
date           2020-11-02T09:37:04 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 20, num_rlzs = 10

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    10                                        
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                2.0                                       
rupture_mesh_spacing            1.0                                       
complex_fault_mesh_spacing      1.0                                       
width_of_mfd_bin                1.0                                       
area_source_discretization      None                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     1067                                      
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== =================== =====================
grp_id gsim                rlzs                 
====== =================== =====================
0      '[AkkarBommer2010]' [3, 4, 7]            
0      '[SadighEtAl1997]'  [0, 1, 2, 5, 6, 8, 9]
====== =================== =====================

Required parameters per tectonic region type
--------------------------------------------
===== ====================================== ========= ========== ==========
et_id gsims                                  distances siteparams ruptparams
===== ====================================== ========= ========== ==========
0     '[AkkarBommer2010]' '[SadighEtAl1997]' rjb rrup  vs30       mag rake  
===== ====================================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         P    1.276E-04 1         3           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    1.276E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      5.376E-04 nan    5.376E-04 5.376E-04
read_source_model  1      0.00175   nan    0.00175   0.00175  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      1.55 KB 
preclassical           239 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47344, maxmem=0.4 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.19002   0.0       1     
composite source model    0.18463   0.0       1     
total read_source_model   0.00175   0.0       1     
total preclassical        5.376E-04 0.0       1     
========================= ========= ========= ======