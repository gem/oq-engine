Probabilistic Event-Based QA Test with Spatial Correlation, case 1
==================================================================

============== ===================
checksum32     3,946,641,235      
date           2018-09-25T14:28:02
engine_version 3.3.0-git8ffb37de56
============== ===================

num_sites = 2, num_levels = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         125               
truncation_level                None              
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        123456789         
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
================ ====== ==================== ============ ============

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      1         P    0     1     1            0.01382   1.645E-05  2.00000   1         18,773
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.01382   1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =========
operation-duration mean      stddev min       max       num_tasks
read_source_models 7.555E-04 NaN    7.555E-04 7.555E-04 1        
split_filter       0.00346   NaN    0.00346   0.00346   1        
build_ruptures     0.01550   NaN    0.01550   0.01550   1        
================== ========= ====== ========= ========= =========

Data transfer
-------------
================== ======================================================================= =========
task               sent                                                                    received 
read_source_models monitor=0 B fnames=0 B converter=0 B                                    1.51 KB  
split_filter       srcs=1.26 KB monitor=432 B srcfilter=220 B sample_factor=21 B seed=14 B 1.3 KB   
build_ruptures     srcs=0 B srcfilter=0 B param=0 B monitor=0 B                            333.05 KB
================== ======================================================================= =========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
saving ruptures          0.07795   0.0       1     
total build_ruptures     0.01550   0.0       1     
updating source_info     0.00926   0.0       1     
store source_info        0.00565   0.0       1     
total split_filter       0.00346   0.0       1     
total read_source_models 7.555E-04 0.0       1     
making contexts          4.828E-04 0.0       1     
======================== ========= ========= ======