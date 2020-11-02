Disaggregation with sampling
============================

============== ====================
checksum32     1_253_230_809       
date           2020-11-02T09:13:10 
engine_version 3.11.0-git24d6ba92cd
============== ====================

num_sites = 2, num_levels = 38, num_rlzs = 2

Parameters
----------
=============================== ========================================
calculation_mode                'preclassical'                          
number_of_logic_tree_samples    2                                       
maximum_distance                {'default': [(1.0, 40.0), (10.0, 40.0)]}
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
=============================== ========================================

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
====== =================== ======
grp_id gsim                rlzs  
====== =================== ======
0      '[ChiouYoungs2008]' [0, 1]
====== =================== ======

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
4         C    0.00216   1         164         
1         P    2.475E-04 1         15          
2         A    1.516E-04 1         1_440       
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    1.516E-04
C    0.00216  
P    2.475E-04
S    0.0      
==== =========

Information about the tasks
---------------------------
================== ====== ======= ====== ========= =======
operation-duration counts mean    stddev min       max    
preclassical       4      0.00180 62%    6.588E-04 0.00314
read_source_model  1      0.00569 nan    0.00569   0.00569
================== ====== ======= ====== ========= =======

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model                                3.07 KB 
preclassical      srcs=5.67 KB srcfilter=5.04 KB 914 B   
================= ============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46897, maxmem=1.1 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.24671  0.00391   1     
composite source model    0.22532  0.00391   1     
total preclassical        0.00720  0.36719   4     
total read_source_model   0.00569  0.0       1     
========================= ======== ========= ======