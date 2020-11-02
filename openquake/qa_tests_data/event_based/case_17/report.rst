Event Based Hazard QA Test, Case 17
===================================

============== ====================
checksum32     517_223_860         
date           2020-11-02T08:41:29 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 1, num_levels = 3, num_rlzs = 5

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    5                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1.0                                       
ses_per_logic_tree_path         3                                         
truncation_level                2.0                                       
rupture_mesh_spacing            2.0                                       
complex_fault_mesh_spacing      2.0                                       
width_of_mfd_bin                1.0                                       
area_source_discretization      20.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     106                                       
master_seed                     0                                         
ses_seed                        106                                       
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
====== ================ ============
grp_id gsim             rlzs        
====== ================ ============
0      [SadighEtAl1997] [0]         
1      [SadighEtAl1997] [1, 2, 3, 4]
====== ================ ============

Required parameters per tectonic region type
--------------------------------------------
===== ================== ========= ========== ==========
et_id gsims              distances siteparams ruptparams
===== ================== ========= ========== ==========
0     '[SadighEtAl1997]' rrup      vs30       mag rake  
1     '[SadighEtAl1997]' rrup      vs30       mag rake  
===== ================== ========= ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
1         P    1.788E-04 1         39          
2         P    1.583E-04 1         7           
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    3.371E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       2      7.463E-04 13%    6.492E-04 8.433E-04
read_source_model  2      0.00136   3%     0.00131   0.00142  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model converter=664 B fname=202 B    3.18 KB 
preclassical      srcfilter=2.56 KB srcs=2.56 KB 478 B   
================= ============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46576, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.04459  0.0       1     
composite source model    1.03918  0.0       1     
total read_source_model   0.00273  0.26562   2     
total preclassical        0.00149  0.20312   2     
========================= ======== ========= ======