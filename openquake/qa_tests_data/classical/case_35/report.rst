Classical Hazard QA Test, Case 35 - Cluster model
=================================================

============== ====================
checksum32     2_932_135_388       
date           2020-11-02T09:14:37 
engine_version 3.11.0-git24d6ba92cd
============== ====================

num_sites = 1, num_levels = 5, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         1                                         
truncation_level                10.0                                      
rupture_mesh_spacing            10.0                                      
complex_fault_mesh_spacing      10.0                                      
width_of_mfd_bin                1.0                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     1066                                      
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====== ================== ====
grp_id gsim               rlzs
====== ================== ====
0      '[SadighEtAl1997]' [0] 
====== ================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ================== ========= ========== ==========
et_id gsims              distances siteparams ruptparams
===== ================== ========= ========== ==========
0     '[SadighEtAl1997]' rrup      vs30       mag rake  
===== ================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         X    1.762E-04 1         1           
0         X    1.752E-04 1         1           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
X    3.514E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       2      6.560E-04 0%     6.545E-04 6.576E-04
read_source_model  1      0.00779   nan    0.00779   0.00779  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model                                3.49 KB 
preclassical      srcs=4.64 KB srcfilter=1.75 KB 478 B   
================= ============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46999, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.06279  0.0       1     
composite source model    0.05818  0.0       1     
total read_source_model   0.00779  0.0       1     
total preclassical        0.00131  0.20312   2     
========================= ======== ========= ======