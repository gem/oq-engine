Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

============== ====================
checksum32     3_167_921_005       
date           2020-11-02T09:37:22 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 3, num_levels = 10, num_rlzs = 12

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            1.0                                       
complex_fault_mesh_spacing      1.0                                       
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
====== ========================= ========
grp_id gsim                      rlzs    
====== ========================= ========
0      '[BooreAtkinson2008]'     [0, 1]  
0      '[CampbellBozorgnia2008]' [2, 3]  
1      '[BooreAtkinson2008]'     [4, 5]  
1      '[CampbellBozorgnia2008]' [6, 7]  
2      '[BooreAtkinson2008]'     [8, 9]  
2      '[CampbellBozorgnia2008]' [10, 11]
3      '[Campbell2003]'          [0, 2]  
3      '[ToroEtAl2002]'          [1, 3]  
====== ========================= ========

Required parameters per tectonic region type
--------------------------------------------
===== =============================================== ========= ========== =================
et_id gsims                                           distances siteparams ruptparams       
===== =============================================== ========= ========== =================
0     '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' rjb rrup  vs30 z2pt5 dip mag rake ztor
1     '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' rjb rrup  vs30 z2pt5 dip mag rake ztor
2     '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' rjb rrup  vs30 z2pt5 dip mag rake ztor
3     '[Campbell2003]' '[ToroEtAl2002]'               rjb rrup             mag              
4     '[Campbell2003]' '[ToroEtAl2002]'               rjb rrup             mag              
5     '[Campbell2003]' '[ToroEtAl2002]'               rjb rrup             mag              
===== =============================================== ========= ========== =================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
2         P    2.005E-04 3         15          
1         P    1.998E-04 3         15          
3;0       A    1.516E-04 3         240         
3;1       A    1.400E-04 3         240         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    2.916E-04
P    4.003E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       4      6.563E-04 2%     6.397E-04 6.804E-04
read_source_model  2      0.00198   14%    0.00170   0.00227  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ============================= ========
task              sent                          received
read_source_model converter=664 B fname=198 B   3.68 KB 
preclassical      srcfilter=6.9 KB srcs=6.37 KB 960 B   
================= ============================= ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47358, maxmem=1.2 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.04712  0.0       1     
composite source model    1.04182  0.0       1     
total read_source_model   0.00397  0.20312   2     
total preclassical        0.00263  0.14062   4     
========================= ======== ========= ======