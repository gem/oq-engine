Classical Hazard QA Test, Case 11
=================================

============== ===================
checksum32     2,496,930,815      
date           2019-07-30T15:04:31
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 3

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.01              
complex_fault_mesh_spacing      0.01              
width_of_mfd_bin                0.001             
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1_b2     0.20000 trivial(1)      1               
b1_b3     0.60000 trivial(1)      1               
b1_b4     0.20000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
2      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3,500        3,000       
source_model.xml 1      Active Shallow Crust 3,000        3,000       
source_model.xml 2      Active Shallow Crust 2,500        3,000       
================ ====== ==================== ============ ============

============= =====
#TRT models   3    
#eff_ruptures 9,000
#tot_ruptures 9,000
============= =====

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ====== =======
source_id grp_id code num_ruptures calc_time num_sites weight speed  
========= ====== ==== ============ ========= ========= ====== =======
1         0      P    3,500        0.01768   3.00000   9,000  509,093
========= ====== ==== ============ ========= ========= ====== =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.01768   3     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00624 0.00121 0.00490 0.00725 3      
read_source_models 0.00534 0.00163 0.00346 0.00632 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================================= ========
task               sent                                                    received
preclassical       srcs=3.51 KB params=1.54 KB srcfilter=660 B gsims=441 B 1 KB    
read_source_models converter=942 B fnames=300 B                            4.68 KB 
================== ======================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15542               time_sec  memory_mb counts
======================== ========= ========= ======
total preclassical       0.01872   0.0       3     
total read_source_models 0.01602   0.0       3     
store source_info        0.00208   0.0       1     
managing sources         0.00107   0.0       1     
aggregate curves         4.609E-04 0.0       3     
======================== ========= ========= ======