GEM model for PAC, 0.10 in 50 years, Suva, testing IDL
======================================================

============== ===================
checksum32     2,604,004,363      
date           2019-10-01T06:08:23
engine_version 3.8.0-gite0871b5c35
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
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
19        0      S    86           0.04257   1.00000   67           1,574
32        0      S    80           0.04195   1.00000   86           2,050
39        0      S    61           0.04009   1.00000   80           1,996
36        0      S    67           0.02897   1.00000   55           1,899
28        0      S    55           0.01923   1.00000   61           3,172
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.17280   5     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.07605 NaN     0.07605 0.07605 1      
preclassical       0.03493 0.01022 0.01956 0.04290 5      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ======================================= ========
task         sent                                    received
SourceReader                                         44.63 KB
preclassical srcs=31 KB params=3.71 KB gsims=1.83 KB 1.67 KB 
============ ======================================= ========

Slowest operations
------------------
====================== ======== ========= ======
calc_23142             time_sec memory_mb counts
====================== ======== ========= ======
total preclassical     0.17466  0.0       5     
composite source model 0.09388  0.0       1     
total SourceReader     0.07605  0.0       1     
store source_info      0.00209  0.0       1     
aggregate curves       0.00118  0.0       5     
====================== ======== ========= ======