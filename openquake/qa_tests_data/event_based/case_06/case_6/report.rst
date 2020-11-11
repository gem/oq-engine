Event-based PSHA producing hazard curves only
=============================================

============== ====================
checksum32     1_125_224_941       
date           2020-11-02T09:35:59 
engine_version 3.11.0-git82b78631ac
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
====== ========================= ====
grp_id gsim                      rlzs
====== ========================= ====
0      '[BooreAtkinson2008]'     [0] 
0      '[CampbellBozorgnia2008]' [1] 
0      '[ChiouYoungs2008]'       [2] 
1      '[BooreAtkinson2008]'     [3] 
1      '[CampbellBozorgnia2008]' [4] 
1      '[ChiouYoungs2008]'       [5] 
====== ========================= ====

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
1;0       A    1.452E-04 1         2_456       
1;1       A    1.414E-04 1         2_456       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    2.866E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       2      6.398E-04 3%     6.163E-04 6.633E-04
read_source_model  2      0.00406   1%     0.00401   0.00410  
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
calc_47279, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.24473  0.05859   1     
composite source model    1.24015  0.05859   1     
total read_source_model   0.00811  0.49609   2     
total preclassical        0.00128  0.50781   2     
========================= ======== ========= ======