Classical Hazard QA Test, Case 11
=================================

============== ===================
checksum32     2,496,930,815      
date           2019-10-01T06:08:57
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 3

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
b1_b2     0.20000 trivial(1)      1               
b1_b3     0.60000 trivial(1)      1               
b1_b4     0.20000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
2      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   3,500        3,500       
1      1.00000   3,000        3,000       
2      1.00000   2,500        2,500       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
1         0      P    3,500        0.00987   1.00000   3,500        354,762
1         1      P    3,000        0.00940   1.00000   3,000        319,315
1         2      P    2,500        0.00338   1.00000   2,500        739,006
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.02264   3     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.01781 0.00485 0.01225 0.02122 3      
preclassical       0.00819 0.00390 0.00369 0.01068 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=3.65 KB ltmodel=576 B fname=291 B 87.39 KB
preclassical srcs=3.47 KB params=1.54 KB srcfilter=669 B 1 KB    
============ =========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_23185             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.05343  0.0       3     
composite source model 0.03967  0.0       1     
total preclassical     0.02456  0.0       3     
store source_info      0.00209  0.0       1     
aggregate curves       0.00137  0.0       3     
====================== ======== ========= ======