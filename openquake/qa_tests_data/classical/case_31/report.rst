Classical PSHA with source specific logic tree (3**2 realizations)
==================================================================

============== ====================
checksum32     2_608_530_546       
date           2020-11-02T09:37:19 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 14, num_rlzs = 9

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
area_source_discretization      10.0                                      
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
====== ===================== =========
grp_id gsim                  rlzs     
====== ===================== =========
0      '[BooreAtkinson2008]' [0, 3, 6]
1      '[BooreAtkinson2008]' [1, 4, 7]
2      '[BooreAtkinson2008]' [2, 5, 8]
3      '[ToroEtAl2002]'      [0, 1, 2]
4      '[ToroEtAl2002]'      [3, 4, 5]
5      '[ToroEtAl2002]'      [6, 7, 8]
====== ===================== =========

Required parameters per tectonic region type
--------------------------------------------
===== ===================== ========= ========== ==========
et_id gsims                 distances siteparams ruptparams
===== ===================== ========= ========== ==========
0     '[BooreAtkinson2008]' rjb       vs30       mag rake  
1     '[BooreAtkinson2008]' rjb       vs30       mag rake  
2     '[BooreAtkinson2008]' rjb       vs30       mag rake  
3     '[BooreAtkinson2008]' rjb       vs30       mag rake  
4     '[BooreAtkinson2008]' rjb       vs30       mag rake  
5     '[BooreAtkinson2008]' rjb       vs30       mag rake  
6     '[BooreAtkinson2008]' rjb       vs30       mag rake  
7     '[BooreAtkinson2008]' rjb       vs30       mag rake  
8     '[BooreAtkinson2008]' rjb       vs30       mag rake  
9     '[ToroEtAl2002]'      rjb                  mag       
10    '[ToroEtAl2002]'      rjb                  mag       
11    '[ToroEtAl2002]'      rjb                  mag       
12    '[ToroEtAl2002]'      rjb                  mag       
13    '[ToroEtAl2002]'      rjb                  mag       
14    '[ToroEtAl2002]'      rjb                  mag       
15    '[ToroEtAl2002]'      rjb                  mag       
16    '[ToroEtAl2002]'      rjb                  mag       
17    '[ToroEtAl2002]'      rjb                  mag       
===== ===================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
2;0       S    0.00198   1         310         
2;2       S    0.00195   1         310         
2;1       S    0.00190   1         310         
1;2       A    1.323E-04 1         1_040       
1;0       A    1.290E-04 1         1_040       
1;1       A    1.268E-04 1         1_040       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    3.881E-04
S    0.00584  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       6      0.00151 60%    5.841E-04 0.00246
read_source_model  1      0.00419 nan    0.00419   0.00419
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model                                2.48 KB 
preclassical      srcs=9.97 KB srcfilter=9.71 KB 1.41 KB 
================= ============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47355, maxmem=1.3 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.16320  0.0       1     
composite source model    0.15633  0.0       1     
total preclassical        0.00904  0.50781   6     
total read_source_model   0.00419  0.0       1     
========================= ======== ========= ======