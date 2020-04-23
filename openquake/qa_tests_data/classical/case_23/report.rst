Classical PSHA with NZ NSHM
===========================

============== ===================
checksum32     3_211_843_635      
date           2020-03-13T11:23:10
engine_version 3.9.0-gitfb3ef3a732
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
====== ===================== ========= ========== ===================
grp_id gsims                 distances siteparams ruptparams         
====== ===================== ========= ========== ===================
0      '[McVerry2006Asc]'    rrup      vs30       hypo_depth mag rake
1      '[McVerry2006SInter]' rrup      vs30       hypo_depth mag rake
====== ===================== ========= ========== ===================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.05000   40           40          
1      1.00000   2            2.00000     
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
21444     1      X    1            0.00286   1.00000   1.00000     
2         0      P    20           0.00257   0.05000   20          
1         0      P    20           0.00255   0.05000   20          
21445     1      X    1            1.626E-04 1.00000   1.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00512  
X    0.00302  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00398 1.368E-04 0.00389 0.00413 3      
read_source_model  0.23033 NaN       0.23033 0.23033 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================= ============================================= =========
task              sent                                          received 
read_source_model                                               808.93 KB
preclassical      srcs=837.85 KB params=2.48 KB srcfilter=669 B 1.12 KB  
================= ============================================= =========

Slowest operations
------------------
=========================== ======== ========= ======
calc_67013                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      0.49074  1.24609   1     
total read_source_model     0.23033  1.06641   1     
total preclassical          0.01193  0.50391   3     
store source_info           0.00252  0.0       1     
splitting/filtering sources 0.00117  0.0       3     
aggregate curves            0.00109  0.0       3     
=========================== ======== ========= ======
