Classical PSHA with NZ NSHM
===========================

============== ====================
checksum32     3_518_996_068       
date           2020-11-02T09:37:39 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 29, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 400.0), (10.0, 400.0)]}
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
====== ===================== ====
grp_id gsim                  rlzs
====== ===================== ====
0      '[McVerry2006Asc]'    [0] 
1      '[McVerry2006SInter]' [0] 
====== ===================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ===================== ========= ========== ===================
et_id gsims                 distances siteparams ruptparams         
===== ===================== ========= ========== ===================
0     '[McVerry2006Asc]'    rrup      vs30       hypo_depth mag rake
1     '[McVerry2006SInter]' rrup      vs30       hypo_depth mag rake
===== ===================== ========= ========== ===================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
21444     X    2.353E-04 1         1           
21445     X    2.072E-04 1         1           
2         P    2.058E-04 1         20          
1         P    1.938E-04 1         20          
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    3.996E-04
X    4.425E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       4      6.902E-04 3%     6.554E-04 7.105E-04
read_source_model  1      0.28159   nan    0.28159   0.28159  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ================================ =========
task              sent                             received 
read_source_model                                  808.91 KB
preclassical      srcs=825.88 KB srcfilter=5.64 KB 964 B    
================= ================================ =========

Slowest operations
------------------
========================= ======== ========= ======
calc_47375, maxmem=1.2 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.67412  1.25391   1     
composite source model    0.66953  1.25391   1     
total read_source_model   0.28159  1.58984   1     
total preclassical        0.00276  0.44141   4     
========================= ======== ========= ======