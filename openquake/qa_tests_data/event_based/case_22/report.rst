Test case for the SplitSigma modified GMPE
==========================================

============== ===================
checksum32     4_125_479_680      
date           2020-03-13T11:20:55
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 36, num_levels = 40, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        24                
=============================== ==================

Input files
-----------
======================= ========================
Name                    File                    
======================= ========================
gsim_logic_tree         `gmmLt.xml <gmmLt.xml>`_
job_ini                 `job.ini <job.ini>`_    
source_model_logic_tree `ssmLt.xml <ssmLt.xml>`_
======================= ========================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================================================== ========= ========== ==========
grp_id gsims                                                                 distances siteparams ruptparams
====== ===================================================================== ========= ========== ==========
0      '[SplitSigmaGMPE]\ngmpe_name = "Campbell2003"\nwithin_absolute = 0.3' rrup                 mag       
====== ===================================================================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      4.50000   416          416         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      A    416          0.00742   4.50000   416         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00742  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.02910 NaN    0.02910 0.02910 1      
read_source_model  0.01275 NaN    0.01275 0.01275 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ====================================== ========
task              sent                                   received
read_source_model                                        2.24 KB 
preclassical      srcs=1.94 KB params=1009 B gsims=743 B 370 B   
================= ====================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66925                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.02910   0.07422   1     
composite source model      0.02071   0.0       1     
splitting/filtering sources 0.02038   0.07422   1     
total read_source_model     0.01275   0.0       1     
store source_info           0.00267   0.0       1     
aggregate curves            2.851E-04 0.0       1     
=========================== ========= ========= ======