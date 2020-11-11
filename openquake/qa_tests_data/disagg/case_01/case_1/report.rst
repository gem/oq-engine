QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============== ====================
checksum32     1_876_684_295       
date           2020-11-02T09:35:41 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 2, num_levels = 38, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 100.0), (10.0, 100.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            5.0                                       
complex_fault_mesh_spacing      5.0                                       
width_of_mfd_bin                0.2                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     9000                                      
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
0      '[ChiouYoungs2008]' [0] 
====== =================== ====

Required parameters per tectonic region type
--------------------------------------------
===== =================== =========== ======================= =================
et_id gsims               distances   siteparams              ruptparams       
===== =================== =========== ======================= =================
0     '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
===== =================== =========== ======================= =================

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
3         S    0.00265   1         617         
4         C    0.00212   1         164         
1         P    2.539E-04 1         30          
2         A    1.485E-04 1         2_880       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    1.485E-04
C    0.00212  
P    2.539E-04
S    0.00265  
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       4      0.00180 61%    6.390E-04 0.00314
read_source_model  1      0.00567 nan    0.00567   0.00567
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model                                3.4 KB  
preclassical      srcs=5.67 KB srcfilter=5.04 KB 956 B   
================= ============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47244, maxmem=1.1 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.19033  0.0       1     
composite source model    0.18534  0.0       1     
total preclassical        0.00722  0.51172   4     
total read_source_model   0.00567  0.0       1     
========================= ======== ========= ======