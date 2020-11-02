Classical Hazard QA Test, Case 12
=================================

============== ====================
checksum32     3_065_275_574       
date           2020-11-02T09:15:10 
engine_version 3.11.0-git24d6ba92cd
============== ====================

num_sites = 1, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                2.0                                       
rupture_mesh_spacing            1.0                                       
complex_fault_mesh_spacing      1.0                                       
width_of_mfd_bin                1.0                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     1066                                      
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
====== ==================================================== ====
grp_id gsim                                                 rlzs
====== ==================================================== ====
0      '[SadighEtAl1997]'                                   [0] 
1      '[NRCan15SiteTerm]\ngmpe_name = "BooreAtkinson2008"' [0] 
====== ==================================================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ==================================================== ========= ========== ==========
et_id gsims                                                distances siteparams ruptparams
===== ==================================================== ========= ========== ==========
0     '[SadighEtAl1997]'                                   rrup      vs30       mag rake  
1     '[NRCan15SiteTerm]\ngmpe_name = "BooreAtkinson2008"' rjb       vs30       mag rake  
===== ==================================================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
2         P    1.628E-04 1         1           
1         P    1.564E-04 1         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    3.192E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       2      6.530E-04 2%     6.361E-04 6.700E-04
read_source_model  1      0.00335   nan    0.00335   0.00335  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ============================ ========
task              sent                         received
read_source_model                              1.85 KB 
preclassical      srcs=2.3 KB srcfilter=1.8 KB 478 B   
================= ============================ ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47028, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.06424  0.0       1     
composite source model    0.05881  0.0       1     
total read_source_model   0.00335  0.0       1     
total preclassical        0.00131  0.20312   2     
========================= ======== ========= ======