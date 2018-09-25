QA test for blocksize independence (hazard)
===========================================

============== ===================
checksum32     2,348,158,649      
date           2018-09-25T14:27:55
engine_version 3.3.0-git8ffb37de56
============== ===================

num_sites = 2, num_levels = 4

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 400.0}
investigation_time              5.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.5               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1024              
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
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 2,625        5,572       
================ ====== ==================== ============ ============

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      1         A    0     4     1,752        1.85509   28         584       292       1.00000
0      2         A    4     8     582          0.55560   2.85070    194       97        3.00000
0      3         A    8     12    440          0.19638   1.44441    114       57        0.0    
0      4         A    12    16    267          0.0       0.0        0.0       0         0.0    
0      5         A    16    20    518          0.0       0.0        0.0       0         0.0    
0      6         A    20    24    316          0.0       0.0        0.0       0         0.0    
0      7         A    24    28    1,028        0.0       0.0        0.0       0         0.0    
0      8         A    28    32    447          0.0       0.0        0.0       0         0.0    
0      9         A    32    36    222          0.00244   0.05608    3.00000   2         0.0    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.60950   9     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
read_source_models 0.61453 NaN     0.61453 0.61453 1        
split_filter       0.62795 NaN     0.62795 0.62795 1        
build_ruptures     0.04639 0.01387 0.02097 0.09166 63       
================== ======= ======= ======= ======= =========

Data transfer
-------------
================== ======================================================================== =========
task               sent                                                                     received 
read_source_models monitor=0 B fnames=0 B converter=0 B                                     9.2 KB   
split_filter       srcs=30.96 KB monitor=432 B srcfilter=220 B sample_factor=21 B seed=14 B 129.54 KB
build_ruptures     srcs=200.07 KB monitor=21.23 KB param=18.15 KB srcfilter=13.54 KB        255.88 KB
================== ======================================================================== =========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total build_ruptures     2.92237  0.13281   63    
updating source_info     0.65254  0.0       1     
total split_filter       0.62795  0.57812   1     
total read_source_models 0.61453  0.0       1     
saving ruptures          0.01041  0.0       4     
making contexts          0.00552  0.0       5     
store source_info        0.00494  0.0       1     
======================== ======== ========= ======