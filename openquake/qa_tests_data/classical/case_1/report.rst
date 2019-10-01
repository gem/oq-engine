Classical Hazard QA Test, Case 1
================================

============== ===================
checksum32     141,718,627        
date           2019-10-01T06:08:44
engine_version 3.8.0-gite0871b5c35
============== ===================

num_sites = 1, num_levels = 6, num_rlzs = 1

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
area_source_discretization      None              
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
0      1.00000   1            1.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
1         0      P    1            0.00104   1.00000   1.00000      960  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00104   1     
==== ========= ======

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =======
operation-duration mean      stddev min       max       outputs
SourceReader       8.800E-04 NaN    8.800E-04 8.800E-04 1      
preclassical       0.00132   NaN    0.00132   0.00132   1      
================== ========= ====== ========= ========= =======

Data transfer
-------------
============ ========================================= ========
task         sent                                      received
SourceReader                                           2.57 KB 
preclassical srcs=1.15 KB params=612 B srcfilter=223 B 342 B   
============ ========================================= ========

Slowest operations
------------------
====================== ========= ========= ======
calc_23169             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.01244   0.0       1     
store source_info      0.00202   0.0       1     
total preclassical     0.00132   0.0       1     
total SourceReader     8.800E-04 0.0       1     
aggregate curves       5.119E-04 0.0       1     
====================== ========= ========= ======