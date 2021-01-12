Classical Hazard QA Test, Case 17
=================================

============== ====================
checksum32     3_298_114_952       
date           2020-11-02T09:37:08 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 1, num_levels = 3, num_rlzs = 5

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    5                                         
maximum_distance                {'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              1000.0                                    
ses_per_logic_tree_path         1                                         
truncation_level                2.0                                       
rupture_mesh_spacing            1.0                                       
complex_fault_mesh_spacing      1.0                                       
width_of_mfd_bin                1.0                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     106                                       
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
====== ================== ===============
grp_id gsim               rlzs           
====== ================== ===============
0      '[SadighEtAl1997]' [0]            
1      '[SadighEtAl1997]' [0, 1, 2, 3, 4]
2      '[SadighEtAl1997]' [1, 2, 3, 4]   
====== ================== ===============

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
A;0       P    1.886E-04 1         39          
A;1       P    1.569E-04 1         7           
B         P    1.559E-04 1         13          
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    5.014E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       3      6.665E-04 2%     6.464E-04 6.905E-04
read_source_model  2      0.00173   2%     0.00169   0.00177  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model converter=664 B fname=198 B    4.06 KB 
preclassical      srcfilter=4.68 KB srcs=3.88 KB 721 B   
================= ============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47349, maxmem=1.1 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.02504  0.0       1     
composite source model    1.01991  0.0       1     
total read_source_model   0.00346  0.60156   2     
total preclassical        0.00200  0.14062   3     
========================= ======== ========= ======