Classical Hazard QA Test, Case 3
================================

============== ===================
checksum32     2,349,244,270      
date           2019-09-24T15:21:25
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      0.1               
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
b1        1.00000 trivial(1)      1               
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
source_model.xml 0      Active Shallow Crust 7,819        7,819       
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ ==========
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed     
========= ====== ==== ============ ========= ========= ============ ==========
1         0      A    7,819        2.341E-04 1.00000   7,819        33,396,398
========= ====== ==== ============ ========= ========= ============ ==========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.341E-04 1     
==== ========= ======

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =======
operation-duration mean      stddev min       max       outputs
preclassical       7.300E-04 NaN    7.300E-04 7.300E-04 1      
read_source_models 1.13725   NaN    1.13725   1.13725   1      
================== ========= ====== ========= ========= =======

Data transfer
-------------
================== ========================================= ========
task               sent                                      received
preclassical       srcs=3.82 KB srcfilter=647 B params=518 B 342 B   
read_source_models converter=314 B fnames=106 B              4.18 KB 
================== ========================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1845                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 1.13725   0.0       1     
store source_info        0.00238   0.0       1     
total preclassical       7.300E-04 0.0       1     
managing sources         4.811E-04 0.0       1     
aggregate curves         2.351E-04 0.0       1     
======================== ========= ========= ======