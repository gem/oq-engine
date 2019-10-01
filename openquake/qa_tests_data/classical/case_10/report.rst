Classical Hazard QA Test, Case 10
=================================

============== ===================
checksum32     4,001,490,780      
date           2019-10-01T06:09:00
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.01              
complex_fault_mesh_spacing      0.01              
width_of_mfd_bin                0.001             
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1_b2     0.50000 trivial(1)      1               
b1_b3     0.50000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   3,000        3,000       
1      1.00000   3,000        3,000       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
1         0      P    3,000        0.00866   1.00000   3,000        346,436
1         1      P    3,000        0.00866   1.00000   3,000        346,484
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.01732   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.01059 3.540E-06 0.01059 0.01059 2      
preclassical       0.00902 1.686E-07 0.00902 0.00902 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.31 KB ltmodel=384 B fname=194 B 58.25 KB
preclassical srcs=2.32 KB params=1.03 KB srcfilter=446 B 684 B   
============ =========================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_23198             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.02986   0.0       1     
total SourceReader     0.02118   0.0       2     
total preclassical     0.01803   0.0       2     
store source_info      0.00207   0.0       1     
aggregate curves       4.094E-04 0.0       2     
====================== ========= ========= ======