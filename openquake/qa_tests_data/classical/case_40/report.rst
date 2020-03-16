Classical PSHA — Area Source
============================

============== ===================
checksum32     347_027_509        
date           2020-03-13T11:22:09
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 16, num_levels = 45, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.2               
area_source_discretization      50.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================================== ========= ========== ==========
grp_id gsims                                                                distances siteparams ruptparams
====== ==================================================================== ========= ========== ==========
0      '[NGAEastGMPETotalSigma]\ngmpe_table="NGAEast_YENIER_ATKINSON.hdf5"' rrup      vs30       mag       
====== ==================================================================== ========= ========== ==========

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      2.00000   8            8.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      A    8            0.00171   2.00000   8.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00171  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00333 NaN    0.00333 0.00333 1      
read_source_model  0.00243 NaN    0.00243 0.00243 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================= ======================================= ========
task              sent                                    received
read_source_model                                         2.24 KB 
preclassical      gsims=1.12 MB srcs=1.94 KB params=978 B 369 B   
================= ======================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66984                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.01540   1.00391   1     
total preclassical          0.00333   1.76172   1     
total read_source_model     0.00243   0.0       1     
store source_info           0.00208   0.0       1     
splitting/filtering sources 0.00114   0.0       1     
aggregate curves            3.192E-04 0.0       1     
=========================== ========= ========= ======