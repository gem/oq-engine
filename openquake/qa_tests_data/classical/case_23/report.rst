Classical PSHA with NZ NSHM
===========================

============== ===================
checksum32     3,211,843,635      
date           2019-10-01T07:01:18
engine_version 3.8.0-gitbd71c2f960
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
21444     1      X    1            0.00229   1.00000   1.00000      436   
1         0      P    20           0.00214   1.00000   20           9,341 
21445     1      X    1            2.668E-04 1.00000   1.00000      3,748 
2         0      P    20           2.470E-04 1.00000   20           80,971
========= ====== ==== ============ ========= ========= ============ ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00239   2     
X    0.00256   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.18946 NaN       0.18946 0.18946 1      
preclassical       0.00301 1.534E-04 0.00290 0.00312 2      
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
calc_6657              time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.19956   0.82812   1     
total SourceReader     0.18946   0.86719   1     
total preclassical     0.00602   0.0       2     
store source_info      0.00242   0.0       1     
aggregate curves       4.563E-04 0.0       2     
====================== ========= ========= ======