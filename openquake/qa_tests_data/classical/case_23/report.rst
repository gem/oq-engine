Classical PSHA with NZ NSHM
===========================

============== ===================
checksum32     3,211,843,635      
date           2019-10-01T06:32:47
engine_version 3.8.0-git66affb82eb
============== ===================

num_sites = 1, num_levels = 29, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
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
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================ ================
smlt_path weight  gsim_logic_tree  num_realizations
========= ======= ================ ================
b1        1.00000 trivial(1,1,0,0) 1               
========= ======= ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ===================
grp_id gsims                 distances siteparams ruptparams         
====== ===================== ========= ========== ===================
0      '[McVerry2006Asc]'    rrup      vs30       hypo_depth mag rake
1      '[McVerry2006SInter]' rrup      vs30       hypo_depth mag rake
====== ===================== ========= ========== ===================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      2.00000   40           40          
1      2.00000   2            2.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed 
========= ====== ==== ============ ========= ========= ============ ======
1         0      P    20           0.00232   1.00000   20           8,620 
21444     1      X    1            0.00228   1.00000   1.00000      438   
2         0      P    20           2.649E-04 1.00000   20           75,505
21445     1      X    1            2.620E-04 1.00000   1.00000      3,816 
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00259   2     
X    0.00254   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.18800 NaN       0.18800 0.18800 1      
preclassical       0.00313 2.057E-05 0.00312 0.00314 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ ============================================= =========
task         sent                                          received 
SourceReader                                               811.95 KB
preclassical srcs=808.95 KB params=1.42 KB srcfilter=444 B 774 B    
============ ============================================= =========

Slowest operations
------------------
====================== ========= ========= ======
calc_6502              time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.19801   0.90625   1     
total SourceReader     0.18800   1.12500   1     
total preclassical     0.00626   0.0       2     
store source_info      0.00251   0.0       1     
aggregate curves       5.732E-04 0.0       2     
====================== ========= ========= ======