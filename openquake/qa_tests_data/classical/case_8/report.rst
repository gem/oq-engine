Classical Hazard QA Test, Case 8
================================

============== ===================
checksum32     3,078,626,546      
date           2019-10-23T16:26:34
engine_version 3.8.0-git2e0d8e6795
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
rupture_mesh_spacing            0.1               
complex_fault_mesh_spacing      0.1               
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
b1_b2     0.30000 trivial(1)      1               
b1_b3     0.30000 trivial(1)      1               
b1_b4     0.40000 trivial(1)      1               
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
0      3.333E-04 3,000        3,000       
1      3.333E-04 3,000        3,000       
2      3.333E-04 3,000        3,000       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         2      P    3,000        0.00466   3.333E-04 3,000       
1         1      P    3,000        0.00441   3.333E-04 3,000       
1         0      P    3,000        0.00424   3.333E-04 3,000       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.01331  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.01582 0.00591   0.01072 0.02230 3      
preclassical       0.00469 2.113E-04 0.00450 0.00492 3      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=3.79 KB ltmodel=576 B fname=309 B 87.45 KB
preclassical srcs=3.43 KB params=1.66 KB srcfilter=669 B 1 KB    
============ =========================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_44529             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.04816   0.0       1     
total SourceReader     0.04747   0.0       3     
total preclassical     0.01408   0.68750   3     
store source_info      0.00230   0.0       1     
aggregate curves       6.709E-04 0.0       3     
====================== ========= ========= ======