Classical Hazard QA Test, Case 11
=================================

============== ===================
checksum32     1,315,577,391      
date           2019-10-23T16:26:48
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
0      2.857E-04 3,500        3,500       
1      3.333E-04 3,000        3,000       
2      4.000E-04 2,500        2,500       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      P    3,500        0.00480   2.857E-04 3,500       
1         1      P    3,000        0.00450   3.333E-04 3,000       
1         2      P    2,500        0.00383   4.000E-04 2,500       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.01314  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.01518 0.00770   0.01044 0.02407 3      
preclassical       0.00464 4.968E-04 0.00409 0.00506 3      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=3.71 KB ltmodel=576 B fname=312 B 87.45 KB
preclassical srcs=3.43 KB params=1.66 KB srcfilter=669 B 1 KB    
============ =========================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_44553             time_sec  memory_mb counts
====================== ========= ========= ======
total SourceReader     0.04554   0.25781   3     
composite source model 0.04262   0.0       1     
total preclassical     0.01392   0.17969   3     
store source_info      0.00231   0.0       1     
aggregate curves       7.088E-04 0.0       3     
====================== ========= ========= ======