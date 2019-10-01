Classical Hazard QA Test, Case 12
=================================

============== ===================
checksum32     662,604,775        
date           2019-10-01T06:32:47
engine_version 3.8.0-git66affb82eb
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
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
b1        1.00000 trivial(1,1)    1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================== ========= ========== ==========
grp_id gsims                                                distances siteparams ruptparams
====== ==================================================== ========= ========== ==========
0      '[SadighEtAl1997]'                                   rrup      vs30       mag rake  
1      '[NRCan15SiteTerm]\ngmpe_name = "BooreAtkinson2008"' rjb       vs30       mag rake  
====== ==================================================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   1            1.00000     
1      1.00000   1            1.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
1         0      P    1            0.00226   1.00000   1.00000      441  
2         1      P    1            0.00206   1.00000   1.00000      485  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00432   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.00131 NaN       0.00131 0.00131 1      
preclassical       0.00265 1.804E-04 0.00253 0.00278 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ ======================================= ========
task         sent                                    received
SourceReader                                         3.62 KB 
preclassical srcs=2.29 KB params=1.01 KB gsims=920 B 684 B   
============ ======================================= ========

Slowest operations
------------------
====================== ========= ========= ======
calc_6499              time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.00924   0.0       1     
total preclassical     0.00531   0.0       2     
store source_info      0.00240   0.0       1     
total SourceReader     0.00131   0.0       1     
aggregate curves       9.370E-04 0.0       2     
====================== ========= ========= ======