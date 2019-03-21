Classical Hazard QA Test, Case 10
=================================

============== ===================
checksum32     4,001,490,780      
date           2019-03-19T10:05:03
engine_version 3.5.0-gitad6b69ea66
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 2

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
b1_b2     0.50000 trivial(1)      1               
b1_b3     0.50000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,'[SadighEtAl1997]': [0]
  1,'[SadighEtAl1997]': [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3,000        3,000       
source_model.xml 1      Active Shallow Crust 3,000        3,000       
================ ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 6,000
#tot_ruptures 6,000
#tot_weight   600  
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
1      1         P    1     2     3,000        0.0       5.484E-06  1.00000   1         300   
0      1         P    0     1     3,000        0.0       2.027E-05  1.00000   1         300   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.0       2     
==== ========= ======

Duplicated sources
------------------
['1']
Found 1 source(s) with the same ID and 1 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.00427 1.387E-04 0.00417 0.00437 2      
split_filter       0.02585 NaN       0.02585 0.02585 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ======================================= ========
task               sent                                    received
read_source_models converter=626 B fnames=214 B            3.13 KB 
split_filter       srcs=1.47 KB srcfilter=253 B dummy=14 B 1.62 KB 
================== ======================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.02585  1.75391   1     
total read_source_models 0.00854  0.61719   2     
======================== ======== ========= ======