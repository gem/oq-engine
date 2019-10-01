Classical Hazard QA Test, Case 35 - Cluster model
=================================================

============== ===================
checksum32     1,518,465,114      
date           2019-10-01T06:32:39
engine_version 3.8.0-git66affb82eb
============== ===================

num_sites = 1, num_levels = 5, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                10.0              
rupture_mesh_spacing            10.0              
complex_fault_mesh_spacing      10.0              
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
b11       1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      2.00000   2            2.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
0         0      X    1            0.00161   1.00000   1.00000      620  
1         0      X    1            0.00124   1.00000   1.00000      808  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.00285   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00563 NaN    0.00563 0.00563 1      
classical          0.04707 NaN    0.04707 0.04707 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ========================================== ========
task         sent                                       received
SourceReader                                            4.99 KB 
classical    group=4.79 KB param=533 B src_filter=222 B 1.3 KB  
============ ========================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_6478              time_sec  memory_mb counts
====================== ========= ========= ======
total classical        0.04707   0.0       1     
composite source model 0.01466   0.0       1     
aggregate curves       0.01128   0.0       1     
total SourceReader     0.00563   0.0       1     
store source_info      0.00264   0.0       1     
make_contexts          6.804E-04 0.0       2     
computing mean_std     4.041E-04 0.0       2     
get_poes               3.817E-04 0.0       2     
====================== ========= ========= ======