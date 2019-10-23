GEM model for PAC, 0.10 in 50 years, Suva, testing IDL
======================================================

============== ===================
checksum32     2,535,319,210      
date           2019-10-23T16:25:59
engine_version 3.8.0-git2e0d8e6795
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
0      0.01433   349          349         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
19        0      S    86           0.05162   0.01163   86          
32        0      S    80           0.02774   0.01250   80          
39        0      S    61           0.02492   0.01639   61          
36        0      S    67           0.01790   0.01493   67          
28        0      S    55           0.01376   0.01818   55          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.13594  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.16147 NaN     0.16147 0.16147 1      
preclassical       0.02747 0.01476 0.01404 0.05193 5      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ======================================= ========
task         sent                                    received
preclassical srcs=31 KB params=3.44 KB gsims=1.83 KB 1.67 KB 
============ ======================================= ========

Slowest operations
------------------
====================== ======== ========= ======
calc_44440             time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.17443  0.0       1     
total SourceReader     0.16147  0.0       1     
total preclassical     0.13736  0.52734   5     
store source_info      0.00223  0.0       1     
aggregate curves       0.00106  0.0       5     
====================== ======== ========= ======