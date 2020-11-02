Event Based Risk QA Test 2
==========================

============== ====================
checksum32     2_301_435_532       
date           2020-11-02T09:14:21 
engine_version 3.11.0-git24d6ba92cd
============== ====================

num_sites = 3, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 100.0), (10.0, 100.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         20                                        
truncation_level                3.0                                       
rupture_mesh_spacing            5.0                                       
complex_fault_mesh_spacing      5.0                                       
width_of_mfd_bin                0.3                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     23                                        
master_seed                     42                                        
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================== ==============================================================
Name                     File                                                          
======================== ==============================================================
exposure                 `exposure.xml <exposure.xml>`_                                
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                  
job_ini                  `job.ini <job.ini>`_                                          
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_  
structural_vulnerability `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_
======================== ==============================================================

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

Exposure model
--------------
=========== =
#assets     4
#taxonomies 3
=========== =

======== ========== ======= ====== === === =========
taxonomy num_assets mean    stddev min max num_sites
RM       2          1.00000 0%     1   1   2        
RC+      1          1.00000 nan    1   1   1        
W/1      1          1.00000 nan    1   1   1        
*ALL*    3          1.33333 35%    1   2   4        
======== ========== ======= ====== === === =========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         P    2.162E-04 1         6           
2         P    2.034E-04 1         6           
3         P    1.915E-04 1         6           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    6.111E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       3      6.881E-04 1%     6.826E-04 6.979E-04
read_source_model  1      0.00267   nan    0.00267   0.00267  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ============================= ========
task              sent                          received
read_source_model                               2.14 KB 
preclassical      srcs=3.5 KB srcfilter=3.25 KB 717 B   
================= ============================= ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46975, maxmem=1.1 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.08026  0.00391   1     
composite source model    0.05484  0.00391   1     
total read_source_model   0.00267  0.0       1     
total preclassical        0.00206  0.35938   3     
reading exposure          0.00173  0.0       1     
========================= ======== ========= ======