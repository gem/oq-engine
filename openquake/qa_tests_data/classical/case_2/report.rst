Classical Hazard QA Test, Case 2
================================

============== ===================
checksum32     2,848,891,951      
date           2019-10-01T06:32:47
engine_version 3.8.0-git66affb82eb
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.001             
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
========================= ============================================================
Name                      File                                                        
========================= ============================================================
gsim_logic_tree           `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                   `job.ini <job.ini>`_                                        
reqv:active shallow crust `lookup_asc.hdf5 <lookup_asc.hdf5>`_                        
reqv:stable shallow crust `lookup_sta.hdf5 <lookup_sta.hdf5>`_                        
source_model_logic_tree   `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
========================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,1)    1               
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

  <RlzsAssoc(size=2, rlzs=1)>

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
2         1      P    3,000        0.00982   1.00000   3,000        305,477
1         0      P    3,000        0.00970   1.00000   3,000        309,368
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.01952   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.01628 NaN       0.01628 0.01628 1      
preclassical       0.01028 8.918E-05 0.01022 0.01035 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ ============================================= ========
task         sent                                          received
SourceReader                                               30.08 KB
preclassical params=441.09 KB srcs=2.32 KB srcfilter=444 B 684 B   
============ ============================================= ========

Slowest operations
------------------
====================== ========= ========= ======
calc_6500              time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.02708   0.0       1     
total preclassical     0.02057   0.50781   2     
total SourceReader     0.01628   0.0       1     
store source_info      0.00268   0.0       1     
aggregate curves       6.428E-04 0.0       2     
====================== ========= ========= ======