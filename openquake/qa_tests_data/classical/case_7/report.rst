Classical Hazard QA Test, Case 7
================================

============== ===================
checksum32     750,810,642        
date           2019-10-01T06:08:56
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 2

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
b1        0.70000 trivial(1)      1               
b2        0.30000 trivial(1)      1               
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
0      2.00000   140          140         
1      1.00000   91           91          
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
1         1      S    91           0.00379   1.00000   91           23,981
1         0      S    91           0.00369   1.00000   91           24,639
2         0      C    49           0.00213   1.00000   49           22,997
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.00213   1     
S    0.00749   2     
==== ========= ======

Duplicated sources
------------------
Found 1 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.06389 0.06451   0.01827 0.10950 2      
preclassical       0.00357 9.686E-04 0.00245 0.00419 3      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.28 KB ltmodel=378 B fname=196 B 5.99 KB 
preclassical srcs=3.29 KB params=1.51 KB srcfilter=669 B 1 KB    
============ =========================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_23182             time_sec  memory_mb counts
====================== ========= ========= ======
total SourceReader     0.12777   0.0       2     
composite source model 0.11871   0.0       1     
total preclassical     0.01070   0.0       3     
store source_info      0.00380   0.0       1     
aggregate curves       6.952E-04 0.0       3     
====================== ========= ========= ======