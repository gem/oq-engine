NNParametric
============

============== ===================
checksum32     34,932,175         
date           2019-10-01T07:01:07
engine_version 3.8.0-gitbd71c2f960
============== ===================

num_sites = 1, num_levels = 19, num_rlzs = 1

Parameters
----------
=============================== =================================
calculation_mode                'preclassical'                   
number_of_logic_tree_samples    0                                
maximum_distance                {'default': [(5, 500), (6, 500)]}
investigation_time              1.0                              
ses_per_logic_tree_path         1                                
truncation_level                2.0                              
rupture_mesh_spacing            2.0                              
complex_fault_mesh_spacing      2.0                              
width_of_mfd_bin                0.1                              
area_source_discretization      5.0                              
ground_motion_correlation_model None                             
minimum_intensity               {}                               
random_seed                     23                               
master_seed                     0                                
ses_seed                        42                               
=============================== =================================

Input files
-----------
======================= ========================
Name                    File                    
======================= ========================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_
job_ini                 `job.ini <job.ini>`_    
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_
======================= ========================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
====== ===================== ========= ========== ==========

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
test      0      N    1            0.00290   1.00000   1.00000      345  
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.00290   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00144 NaN    0.00144 0.00144 1      
preclassical       0.00343 NaN    0.00343 0.00343 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ========================================= ========
task         sent                                      received
SourceReader                                           3.48 KB 
preclassical srcs=1.81 KB params=647 B srcfilter=236 B 342 B   
============ ========================================= ========

Slowest operations
------------------
====================== ========= ========= ======
calc_6622              time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.01042   0.0       1     
total preclassical     0.00343   0.00781   1     
store source_info      0.00245   0.0       1     
total SourceReader     0.00144   0.0       1     
aggregate curves       2.570E-04 0.0       1     
====================== ========= ========= ======