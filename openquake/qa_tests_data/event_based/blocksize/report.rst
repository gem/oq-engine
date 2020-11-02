QA test for blocksize independence (hazard)
===========================================

============== ====================
checksum32     350_185_793         
date           2020-11-02T09:13:30 
engine_version 3.11.0-git24d6ba92cd
============== ====================

num_sites = 2, num_levels = 4, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    1                                         
maximum_distance                {'default': [(1.0, 400.0), (10.0, 400.0)]}
investigation_time              5.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            20.0                                      
complex_fault_mesh_spacing      20.0                                      
width_of_mfd_bin                0.5                                       
area_source_discretization      20.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     42                                        
master_seed                     0                                         
ses_seed                        1024                                      
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
8         A    1.609E-04 1         447         
3         A    1.488E-04 2         440         
1         A    1.435E-04 2         1_752       
2         A    1.369E-04 2         582         
9         A    1.342E-04 2         222         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    7.243E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       9      5.959E-04 6%     5.419E-04 6.442E-04
read_source_model  1      0.01311   nan    0.01311   0.01311  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model                                5.35 KB 
preclassical      srcs=18.9 KB srcfilter=9.28 KB 1.94 KB 
================= ============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46934, maxmem=1.4 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.06330  0.0       1     
composite source model    1.05861  0.0       1     
total read_source_model   0.01311  0.0       1     
total preclassical        0.00536  0.46094   9     
========================= ======== ========= ======