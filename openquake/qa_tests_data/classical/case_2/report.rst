Classical Hazard QA Test, Case 2
================================

============== ===================
checksum32     2,848,891,951      
date           2019-10-02T10:07:41
engine_version 3.8.0-git6f03622c6e
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
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      P    3,000        0.01078   3.333E-04 3,000       
2         1      P    3,000        0.00992   3.333E-04 3,000       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.02069   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.01652 NaN       0.01652 0.01652 1      
preclassical       0.01084 5.251E-04 0.01046 0.01121 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ ============================================= ========
task         sent                                          received
SourceReader                                               30.16 KB
preclassical params=441.09 KB srcs=2.32 KB srcfilter=446 B 684 B   
============ ============================================= ========

Slowest operations
------------------
====================== ========= ========= ======
calc_29542             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.02917   0.0       1     
total preclassical     0.02167   0.25781   2     
total SourceReader     0.01652   0.0       1     
store source_info      0.00263   0.0       1     
aggregate curves       5.751E-04 0.0       2     
====================== ========= ========= ======