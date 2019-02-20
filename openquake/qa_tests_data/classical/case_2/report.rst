Classical Hazard QA Test, Case 2
================================

============== ===================
checksum32     2,848,891,951      
date           2019-02-18T08:38:18
engine_version 3.4.0-git9883ae17a5
============== ===================

num_sites = 1, num_levels = 4

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
width_of_mfd_bin                0.001             
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
========================= ============================================================
Name                      File                                                        
========================= ============================================================
gsim_logic_tree           `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                   `job.ini <job.ini>`_                                        
reqv:active shallow crust `lookup_asc.hdf5 <lookup_asc.hdf5>`_                        
reqv:stable shallow crust `lookup_sta.hdf5 <lookup_sta.hdf5>`_                        
source_model_logic_tree   `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
========================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,1)    1               
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

  <RlzsAssoc(size=2, rlzs=1)
  0,'[SadighEtAl1997]': [0]
  1,'[SadighEtAl1997]': [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3,000        3,000       
source_model.xml 1      Stable Shallow Crust 3,000        3,000       
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
1      2         P    1     2     3,000        0.0       1.931E-05  1.00000   1         300   
0      1         P    0     1     3,000        0.0       2.170E-05  1.00000   1         300   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.0       2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
read_source_models 0.00760 NaN       0.00760 0.00760 1      
split_filter       0.00548 7.468E-05 0.00542 0.00553 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ====================================== ========
task               sent                                   received
read_source_models converter=305 B fnames=106 B           2.06 KB 
split_filter       srcs=1.15 KB srcfilter=253 B seed=14 B 2.5 KB  
================== ====================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.01096  1.75781   2     
total read_source_models 0.00760  0.49609   1     
======================== ======== ========= ======