Classical PSHA using Alaska 2007 active shallow crust grid model
================================================================

============== ===================
checksum32     4,152,338,418      
date           2019-10-01T06:08:54
engine_version 3.8.0-gite0871b5c35
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.00000   160          160         
1      21        1,104        1,104       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
2         1      M    1,104        0.00384   21        1,104        287,253
1         0      M    160          0.00360   3.00000   160          44,496 
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
M    0.00744   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.00231 0.00122   0.00145 0.00318 2      
preclassical       0.00403 1.669E-04 0.00391 0.00415 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ ========================================== ========
task         sent                                       received
SourceReader apply_unc=2.3 KB ltmodel=492 B fname=213 B 14.72 KB
preclassical srcs=5.96 KB params=3.45 KB gsims=1.07 KB  684 B   
============ ========================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_23178             time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 0.01780   0.0       1     
total preclassical     0.00807   0.0       2     
total SourceReader     0.00462   0.0       2     
store source_info      0.00208   0.0       1     
aggregate curves       4.141E-04 0.0       2     
====================== ========= ========= ======