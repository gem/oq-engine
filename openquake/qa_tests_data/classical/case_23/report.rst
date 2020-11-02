Classical PSHA with NZ NSHM
===========================

============== ====================
checksum32     3_518_996_068       
date           2020-11-02T08:42:59 
engine_version 3.11.0-gitd13380ddb1
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
====== =================== ====
grp_id gsim                rlzs
====== =================== ====
0      [McVerry2006Asc]    [0] 
1      [McVerry2006SInter] [0] 
====== =================== ====

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
21444     X    2.332E-04 1         1           
21445     X    2.151E-04 1         1           
2         P    2.105E-04 1         20          
1         P    1.950E-04 1         20          
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    4.056E-04
X    4.482E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       4      7.044E-04 5%     6.490E-04 7.451E-04
read_source_model  1      0.21506   nan    0.21506   0.21506  
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
calc_46661, maxmem=1.2 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.71071  1.40625   1     
composite source model    0.70593  1.40625   1     
total read_source_model   0.21506  1.25000   1     
total preclassical        0.00282  0.14062   4     
========================= ======== ========= ======