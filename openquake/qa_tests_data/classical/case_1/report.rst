Classical Hazard QA Test, Case 1
================================

============== ===================
checksum32     141,718,627        
date           2019-09-24T15:21:22
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 6, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      None              
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
b11       1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =====
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed
========= ====== ==== ============ ========= ========= ============ =====
1         0      P    1            2.820E-04 1.00000   1.00000      3,545
========= ====== ==== ============ ========= ========= ============ =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    2.820E-04 1     
==== ========= ======

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =======
operation-duration mean      stddev min       max       outputs
preclassical       7.856E-04 NaN    7.856E-04 7.856E-04 1      
read_source_models 0.00155   NaN    0.00155   0.00155   1      
================== ========= ====== ========= ========= =======

Data transfer
-------------
================== ========================================= ========
task               sent                                      received
preclassical       srcs=1.17 KB srcfilter=647 B params=612 B 342 B   
read_source_models converter=306 B fnames=106 B              1.56 KB 
================== ========================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1838                time_sec  memory_mb counts
======================== ========= ========= ======
store source_info        0.00208   0.0       1     
total read_source_models 0.00155   0.0       1     
total preclassical       7.856E-04 0.0       1     
managing sources         3.057E-04 0.0       1     
aggregate curves         2.067E-04 0.0       1     
======================== ========= ========= ======