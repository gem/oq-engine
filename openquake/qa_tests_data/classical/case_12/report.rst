Classical Hazard QA Test, Case 12
=================================

============== ====================
checksum32     3_065_275_574       
date           2020-11-02T09:37:37 
engine_version 3.11.0-git82b78631ac
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
1         P    1.624E-04 1         1           
2         P    1.409E-04 1         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    3.033E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       2      6.009E-04 4%     5.729E-04 6.289E-04
read_source_model  1      0.00286   nan    0.00286   0.00286  
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
calc_47372, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.05831  0.0       1     
composite source model    0.05336  0.0       1     
total read_source_model   0.00286  0.0       1     
total preclassical        0.00120  0.14062   2     
========================= ======== ========= ======