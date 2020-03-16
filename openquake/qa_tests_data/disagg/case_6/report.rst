GEM model for PAC, 0.10 in 50 years, Suva, testing IDL
======================================================

============== ===================
checksum32     393_343_011        
date           2020-03-13T11:20:19
engine_version 3.9.0-gitfb3ef3a732
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
pointsource_distance            {'default': {}}   
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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 3               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ======================= ============================
grp_id gsims                                                         distances   siteparams              ruptparams                  
====== ============================================================= =========== ======================= ============================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ============================================================= =========== ======================= ============================

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
19        0      S    86           0.13280   0.08140   86          
32        0      S    80           0.12903   0.08750   80          
36        0      S    67           0.10086   0.08955   67          
39        0      S    61           0.09845   0.09836   61          
28        0      S    55           0.09130   0.12727   55          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.55244  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.11136 0.01902 0.09219 0.13366 5      
read_source_model  0.07183 NaN     0.07183 0.07183 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model                                            28.33 KB
preclassical      srcs=33.65 KB params=3.79 KB gsims=1.83 KB 1.8 KB  
================= ========================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66890                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          0.55681  1.80078   5     
composite source model      0.20040  0.0       1     
total read_source_model     0.07183  0.0       1     
store source_info           0.00308  0.0       1     
splitting/filtering sources 0.00153  0.0       5     
aggregate curves            0.00139  0.0       5     
=========================== ======== ========= ======