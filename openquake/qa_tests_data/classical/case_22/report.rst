Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

============== ===================
checksum32     4,152,338,418      
date           2019-09-24T15:21:14
engine_version 3.7.0-git749bb363b3
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
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
2         1      M    1,104        0.00137   21        1,104        803,769
1         0      M    160          6.502E-04 3.00000   160          246,090
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
M    0.00202   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00154 5.090E-04 0.00118 0.00190 2      
read_source_models 0.00197 0.00133   0.00103 0.00291 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ============================================= ========
task               sent                                          received
preclassical       srcs=5.99 KB params=3.45 KB srcfilter=2.71 KB 684 B   
read_source_models converter=628 B fnames=233 B                  6.85 KB 
================== ============================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1812                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.00393   0.0       2     
total preclassical       0.00308   0.0       2     
store source_info        0.00210   0.0       1     
aggregate curves         7.238E-04 0.0       2     
managing sources         3.924E-04 0.0       1     
======================== ========= ========= ======