Classical PSHA — Area Source
============================

============== ====================
checksum32     3_361_561_195       
date           2020-11-02T09:36:48 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 19, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                0.2                                       
area_source_discretization      5.0                                       
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
====== ===================== ====
grp_id gsim                  rlzs
====== ===================== ====
0      '[BooreAtkinson2008]' [0] 
====== ===================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ===================== ========= ========== ==========
et_id gsims                 distances siteparams ruptparams
===== ===================== ========= ========== ==========
0     '[BooreAtkinson2008]' rjb       vs30       mag rake  
===== ===================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         A    1.199E-04 1         11_132      
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    1.199E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       1      5.367E-04 nan    5.367E-04 5.367E-04
read_source_model  1      0.00277   nan    0.00277   0.00277  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ==== ========
task              sent received
read_source_model      1.8 KB  
preclassical           239 B   
================= ==== ========

Slowest operations
------------------
========================= ========= ========= ======
calc_47321, maxmem=0.4 GB time_sec  memory_mb counts
========================= ========= ========= ======
importing inputs          0.18195   0.0       1     
composite source model    0.17720   0.0       1     
total read_source_model   0.00277   0.0       1     
total preclassical        5.367E-04 0.0       1     
========================= ========= ========= ======