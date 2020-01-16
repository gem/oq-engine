GEM model for PAC, 0.10 in 50 years, Suva, testing IDL
======================================================

============== ===================
checksum32     2_943_479_776      
date           2020-01-16T05:30:43
engine_version 3.8.0-git83c45f7244
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
pointsource_distance            {'default': 50}   
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
0      0.09456   349          349         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
32        0      S    80           0.14378   0.08750   80          
19        0      S    86           0.13644   0.08140   86          
36        0      S    67           0.11252   0.08955   67          
39        0      S    61           0.10742   0.09836   61          
28        0      S    55           0.10042   0.12727   55          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.60059  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.13604 NaN     0.13604 0.13604 1      
preclassical       0.12115 0.01890 0.10162 0.14478 5      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =============================================== ========
task         sent                                            received
SourceReader                                                 31.93 KB
preclassical params=31.58 KB srcs=31.08 KB srcfilter=6.02 KB 1.79 KB 
============ =============================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_43223                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          0.60573  0.49219   5     
composite source model      0.14806  0.08203   1     
total SourceReader          0.13604  0.08203   1     
store source_info           0.00236  0.0       1     
splitting/filtering sources 0.00216  0.0       5     
aggregate curves            0.00111  0.0       5     
=========================== ======== ========= ======