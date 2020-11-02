Event-based PSHA producing hazard curves only
=============================================

============== ====================
checksum32     1_125_224_941       
date           2020-11-02T08:41:19 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 1, num_levels = 5, num_rlzs = 6

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         30                                        
truncation_level                3.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                0.2                                       
area_source_discretization      20.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     42                                        
master_seed                     0                                         
ses_seed                        23                                        
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
====== ======================= ====
grp_id gsim                    rlzs
====== ======================= ====
0      [BooreAtkinson2008]     [0] 
0      [CampbellBozorgnia2008] [1] 
0      [ChiouYoungs2008]       [2] 
1      [BooreAtkinson2008]     [3] 
1      [CampbellBozorgnia2008] [4] 
1      [ChiouYoungs2008]       [5] 
====== ======================= ====

Required parameters per tectonic region type
--------------------------------------------
===== =================================================================== =========== ============================= =================
et_id gsims                                                               distances   siteparams                    ruptparams       
===== =================================================================== =========== ============================= =================
0     '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
1     '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip mag rake ztor
===== =================================================================== =========== ============================= =================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1;0       A    1.407E-04 1         2_456       
1;1       A    1.295E-04 1         2_456       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    2.701E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       2      6.293E-04 0%     6.232E-04 6.354E-04
read_source_model  2      0.00411   1%     0.00405   0.00417  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model converter=664 B fname=198 B    5.33 KB 
preclassical      srcs=9.98 KB srcfilter=2.06 KB 482 B   
================= ============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46565, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.23250  0.05078   1     
composite source model    1.22798  0.05078   1     
total read_source_model   0.00822  0.46484   2     
total preclassical        0.00126  0.36328   2     
========================= ======== ========= ======