Event Based QA Test, Case 1
===========================

============== ===================
checksum32     1,495,353,520      
date           2018-09-25T14:28:04
engine_version 3.3.0-git8ffb37de56
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         2000              
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1066              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
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
====== =========== ========= ========== ==========
grp_id gsims       distances siteparams ruptparams
====== =========== ========= ========== ==========
0      PGA:SA(0.1) rrup      vs30       mag rake  
====== =========== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,MultiGMPE(gsim_by_imt=OrderedDict([('PGA', 'SadighEtAl1997()'), ('SA(0.1)', 'SadighEtAl1997()')])): [0]>

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
0      1         P    0     1     1            0.00957   1.168E-05  1.00000   1         2,037 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00957   1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =========
operation-duration mean      stddev min       max       num_tasks
read_source_models 7.346E-04 NaN    7.346E-04 7.346E-04 1        
split_filter       0.00256   NaN    0.00256   0.00256   1        
build_ruptures     0.01109   NaN    0.01109   0.01109   1        
================== ========= ====== ========= ========= =========

Data transfer
-------------
================== ======================================================================= ========
task               sent                                                                    received
read_source_models monitor=0 B fnames=0 B converter=0 B                                    1.54 KB 
split_filter       srcs=1.26 KB monitor=432 B srcfilter=220 B sample_factor=21 B seed=14 B 1.29 KB 
build_ruptures     srcs=0 B srcfilter=0 B param=0 B monitor=0 B                            38.83 KB
================== ======================================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total build_ruptures     0.01109   0.0       1     
saving ruptures          0.01033   0.0       1     
updating source_info     0.00751   0.0       1     
store source_info        0.00473   0.0       1     
total split_filter       0.00256   0.0       1     
total read_source_models 7.346E-04 0.0       1     
making contexts          2.918E-04 0.0       1     
======================== ========= ========= ======