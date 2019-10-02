Classical PSHA — Area Source
============================

============== ===================
checksum32     3,698,079,752      
date           2019-10-02T10:07:30
engine_version 3.8.0-git6f03622c6e
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
0      16        8            8.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      A    8            0.00216   2.00000   8.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00216   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       0.00301 NaN    0.00301 0.00301 1      
preclassical       0.00269 NaN    0.00269 0.00269 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ======================================= ========
task         sent                                    received
SourceReader                                         3.53 KB 
preclassical gsims=1.12 MB srcs=1.92 KB params=860 B 342 B   
============ ======================================= ========

Slowest operations
------------------
====================== ========= ========= ======
calc_29517             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.01947   0.77344   1     
total SourceReader     0.00301   0.0       1     
total preclassical     0.00269   0.0       1     
store source_info      0.00256   0.0       1     
aggregate curves       2.692E-04 0.0       1     
====================== ========= ========= ======