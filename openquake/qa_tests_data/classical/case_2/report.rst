Classical Hazard QA Test, Case 2
================================

============== ===================
checksum32     4_177_765_270      
date           2020-01-16T05:31:56
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            {'default': 0}    
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
0      3.333E-04 3_000        3_000       
1      3.333E-04 3_000        3_000       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      P    3_000        0.00531   3.333E-04 3_000       
2         1      P    3_000        0.00473   3.333E-04 3_000       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.01005  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.01749 NaN       0.01749 0.01749 1      
preclassical       0.00589 6.963E-05 0.00584 0.00594 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =============================================== ========
task         sent                                            received
SourceReader                                                 26.11 KB
preclassical params=3.79 MB srcfilter=486.94 KB srcs=2.32 KB 734 B   
============ =============================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43340                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.03069   0.0       1     
total SourceReader          0.01749   0.0       1     
total preclassical          0.01178   0.0       2     
store source_info           0.00239   0.0       1     
splitting/filtering sources 8.481E-04 0.0       2     
aggregate curves            6.299E-04 0.0       2     
=========================== ========= ========= ======