Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

============== ===================
checksum32     4,152,338,418      
date           2019-07-30T15:04:29
engine_version 3.7.0-git3b3dff46da
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
========================= ======= =============== ================
smlt_path                 weight  gsim_logic_tree num_realizations
========================= ======= =============== ================
Alaska_asc_grid_NSHMP2007 1.00000 simple(4)       4               
========================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =============================================================================================================== ========= ========== =======================
grp_id gsims                                                                                                           distances siteparams ruptparams             
====== =============================================================================================================== ========= ========== =======================
0      '[AbrahamsonSilva1997]' '[CampbellBozorgnia2003NSHMP2007]' '[SadighEtAl1997]' '[YoungsEtAl1997SInterNSHMP2008]' rjb rrup  vs30       dip hypo_depth mag rake
1      '[AbrahamsonSilva1997]' '[CampbellBozorgnia2003NSHMP2007]' '[SadighEtAl1997]' '[YoungsEtAl1997SInterNSHMP2008]' rjb rrup  vs30       dip hypo_depth mag rake
====== =============================================================================================================== ========= ========== =======================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=32, rlzs=4)>

Number of ruptures per tectonic region type
-------------------------------------------
==================================================== ====== ==================== ============ ============
source_model                                         grp_id trt                  eff_ruptures tot_ruptures
==================================================== ====== ==================== ============ ============
Alaska_asc_grid_NSHMP2007.xml extra_source_model.xml 0      Active Shallow Crust 160          160         
Alaska_asc_grid_NSHMP2007.xml extra_source_model.xml 1      Active Shallow Crust 1,104        1,104       
==================================================== ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 1,264
#tot_ruptures 1,264
============= =====

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ====== =======
source_id grp_id code num_ruptures calc_time num_sites weight speed  
========= ====== ==== ============ ========= ========= ====== =======
2         1      M    1,104        0.00225   21        1,104  491,249
1         0      M    160          0.00193   3.00000   160    82,820 
========= ====== ==== ============ ========= ========= ====== =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
M    0.00418   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ========= ======= =======
operation-duration mean    stddev    min       max     outputs
preclassical       0.00243 1.932E-04 0.00229   0.00256 2      
read_source_models 0.00109 2.940E-04 8.843E-04 0.00130 2      
================== ======= ========= ========= ======= =======

Data transfer
-------------
================== ========================================================= ========
task               sent                                                      received
preclassical       srcs=5.98 KB params=3.45 KB gsims=1.07 KB srcfilter=440 B 684 B   
read_source_models converter=628 B fnames=219 B                              6.84 KB 
================== ========================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15536               time_sec  memory_mb counts
======================== ========= ========= ======
total preclassical       0.00485   0.0       2     
total read_source_models 0.00218   0.0       2     
store source_info        0.00203   0.0       1     
managing sources         0.00136   0.0       1     
aggregate curves         2.818E-04 0.0       2     
======================== ========= ========= ======