Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

============== ===================
checksum32     2_520_228_386      
date           2020-03-13T11:22:00
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 21, num_levels = 114, num_rlzs = 4

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
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
site_model              `sites.csv <sites.csv>`_                                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========================= ======= ================
smlt_path                 weight  num_realizations
========================= ======= ================
Alaska_asc_grid_NSHMP2007 1.00000 4               
========================= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== =============================================================================================================== ========= ========== =======================
grp_id gsims                                                                                                           distances siteparams ruptparams             
====== =============================================================================================================== ========= ========== =======================
0      '[AbrahamsonSilva1997]' '[CampbellBozorgnia2003NSHMP2007]' '[SadighEtAl1997]' '[YoungsEtAl1997SInterNSHMP2008]' rjb rrup  vs30       dip hypo_depth mag rake
====== =============================================================================================================== ========= ========== =======================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.01359   1_264        368         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
2         0      M    1_104        0.00214   0.01359   368         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
M    0.00214  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00351 0.00136   0.00255 0.00446 2      
read_source_model  0.00400 6.639E-04 0.00353 0.00447 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================= ========================================= ========
task              sent                                      received
read_source_model converter=664 B fname=213 B srcfilter=8 B 6.61 KB 
preclassical      srcs=6.42 KB params=3.68 KB gsims=1.07 KB 694 B   
================= ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66972                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.06165   0.06250   1     
total read_source_model     0.00800   0.0       2     
total preclassical          0.00701   1.42578   2     
store source_info           0.00229   0.0       1     
splitting/filtering sources 0.00117   0.0       2     
aggregate curves            1.936E-04 0.0       1     
=========================== ========= ========= ======