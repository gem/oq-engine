Classical Hazard QA Test, Case 2
================================

============== ===================
checksum32     2,848,891,951      
date           2019-10-01T06:08:57
engine_version 3.8.0-gite0871b5c35
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
1         0      P    3,000        0.00403   1.00000   3,000        744,948
2         1      P    3,000        0.00398   1.00000   3,000        754,281
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00800   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.01825 NaN       0.01825 0.01825 1      
preclassical       0.00428 4.316E-05 0.00425 0.00431 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ ============================================= ========
task         sent                                          received
SourceReader                                               30.07 KB
preclassical params=441.09 KB srcs=2.32 KB srcfilter=446 B 684 B   
============ ============================================= ========

Slowest operations
------------------
====================== ========= ========= ======
calc_23188             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.03112   0.0       1     
total SourceReader     0.01825   0.0       1     
total preclassical     0.00856   0.0       2     
store source_info      0.00373   0.0       1     
aggregate curves       4.959E-04 0.0       2     
====================== ========= ========= ======