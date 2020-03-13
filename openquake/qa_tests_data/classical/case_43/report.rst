Spinning with maximum_distance=60 km
====================================

============== ===================
checksum32     157_333_517        
date           2020-03-13T11:22:05
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 82, num_levels = 20, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.1               
area_source_discretization      150.0             
pointsource_distance            {'default': 100}  
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ==============================
Name                    File                          
======================= ==============================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_      
job_ini                 `job.ini <job.ini>`_          
sites                   `sites_RG.csv <sites_RG.csv>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_      
======================= ==============================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================== ============ ========== ==========
grp_id gsims                  distances    siteparams ruptparams
====== ====================== ============ ========== ==========
0      '[YuEtAl2013MwStable]' azimuth repi            mag       
====== ====================== ============ ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.76944   780          720         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
156       0      A    780          0.00315   0.76944   720         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00315  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.01982 NaN    0.01982 0.01982 1      
read_source_model  0.01398 NaN    0.01398 0.01398 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= =========================================== ========
task              sent                                        received
read_source_model                                             3.33 KB 
preclassical      srcs=3.73 KB params=1.51 KB srcfilter=223 B 370 B   
================= =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66978                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.02362   0.0       1     
total preclassical          0.01982   0.74609   1     
splitting/filtering sources 0.01576   0.0       1     
total read_source_model     0.01398   0.0       1     
store source_info           0.00216   0.0       1     
aggregate curves            4.063E-04 0.0       1     
=========================== ========= ========= ======