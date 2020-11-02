Event Based QA Test, Case 3
===========================

============== ====================
checksum32     3_971_019_167       
date           2020-11-02T09:13:56 
engine_version 3.11.0-git24d6ba92cd
============== ====================

num_sites = 1, num_levels = 3, num_rlzs = 2

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              2.0                                       
ses_per_logic_tree_path         2                                         
truncation_level                2.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                1.0                                       
area_source_discretization      20.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     42                                        
master_seed                     0                                         
ses_seed                        1066                                      
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
====== =================== ====
grp_id gsim                rlzs
====== =================== ====
0      '[AkkarBommer2010]' [1] 
0      '[SadighEtAl1997]'  [0] 
====== =================== ====

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
1         P    1.419E-04 1         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    1.419E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      5.760E-04 nan    5.760E-04 5.760E-04
read_source_model  1      0.00142   nan    0.00142   0.00142  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      1.46 KB 
preclassical           239 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_46954, maxmem=0.3 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.06416   0.0       1     
composite source model    0.05934   0.0       1     
total read_source_model   0.00142   0.0       1     
total preclassical        5.760E-04 0.0       1     
========================= ========= ========= ======