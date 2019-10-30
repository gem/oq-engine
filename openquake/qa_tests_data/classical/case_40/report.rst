Classical PSHA — Area Source
============================

============== ===================
checksum32     3,698,079,752      
date           2019-10-23T16:26:34
engine_version 3.8.0-git2e0d8e6795
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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================= ========= ========== ==========
grp_id gsims                                   distances siteparams ruptparams
====== ======================================= ========= ========== ==========
0      '[YenierAtkinson2015NGAEastTotalSigma]' rrup                 mag       
====== ======================================= ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

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
1         0      A    8            0.00119   2.00000   8.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00119  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00271 NaN    0.00271 0.00271 1      
preclassical       0.00145 NaN    0.00145 0.00145 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ======================================= ========
task         sent                                    received
preclassical gsims=1.12 MB srcs=1.92 KB params=902 B 342 B   
============ ======================================= ========

Slowest operations
------------------
====================== ========= ========= ======
calc_44530             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.03346   1.00391   1     
total SourceReader     0.00271   0.0       1     
store source_info      0.00225   0.0       1     
total preclassical     0.00145   0.0       1     
aggregate curves       2.275E-04 0.0       1     
====================== ========= ========= ======