GEM model for PAC, 0.10 in 50 years, Suva, testing IDL
======================================================

============== ===================
checksum32     2,604,004,363      
date           2019-10-02T10:07:12
engine_version 3.8.0-git6f03622c6e
============== ===================

num_sites = 1, num_levels = 20, num_rlzs = 3

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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
b1        1.00000 simple(3,0,0)   3               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ======================= ============================
grp_id gsims                                                         distances   siteparams              ruptparams                  
====== ============================================================= =========== ======================= ============================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ============================================================= =========== ======================= ============================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=9, rlzs=3)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      5.00000   349          349         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
32        0      S    80           0.02602   0.01250   80          
36        0      S    67           0.02586   0.01493   67          
19        0      S    86           0.02569   0.01163   86          
39        0      S    61           0.02262   0.01639   61          
28        0      S    55           0.02103   0.01818   55          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.12122   5     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.10014 NaN     0.10014 0.10014 1      
preclassical       0.02462 0.00228 0.02141 0.02644 5      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ======================================= ========
task         sent                                    received
SourceReader                                         47.36 KB
preclassical srcs=31 KB params=3.71 KB gsims=1.83 KB 1.67 KB 
============ ======================================= ========

Slowest operations
------------------
====================== ======== ========= ======
calc_29431             time_sec memory_mb counts
====================== ======== ========= ======
total preclassical     0.12312  0.48438   5     
composite source model 0.11153  0.0       1     
total SourceReader     0.10014  0.0       1     
store source_info      0.00293  0.98438   1     
aggregate curves       0.00176  0.0       5     
====================== ======== ========= ======