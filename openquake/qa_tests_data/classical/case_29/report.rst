NNParametric
============

============== ===================
checksum32     34,932,175         
date           2019-02-03T09:39:21
engine_version 3.4.0-gite8c42e513a
============== ===================

num_sites = 1, num_levels = 19

Parameters
----------
=============================== =================================
calculation_mode                'preclassical'                   
number_of_logic_tree_samples    0                                
maximum_distance                {'default': [(5, 500), (6, 500)]}
investigation_time              1.0                              
ses_per_logic_tree_path         1                                
truncation_level                2.0                              
rupture_mesh_spacing            2.0                              
complex_fault_mesh_spacing      2.0                              
width_of_mfd_bin                0.1                              
area_source_discretization      5.0                              
ground_motion_correlation_model None                             
minimum_intensity               {}                               
random_seed                     23                               
master_seed                     0                                
ses_seed                        42                               
=============================== =================================

Input files
-----------
======================= ========================
Name                    File                    
======================= ========================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_
job_ini                 `job.ini <job.ini>`_    
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_
======================= ========================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
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
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      test      N    0     4     1            0.0       1.049E-05  1.00000   1         1.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    0.0       1     
==== ========= ======

Duplicated sources
------------------
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.00159 NaN    0.00159 0.00159 1      
split_filter       0.00291 NaN    0.00291 0.00291 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ====================================== ========
task               sent                                   received
read_source_models converter=313 B fnames=107 B           2.28 KB 
split_filter       srcs=1.81 KB srcfilter=267 B seed=14 B 1.83 KB 
================== ====================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.00291  1.82812   1     
total read_source_models 0.00159  0.15625   1     
======================== ======== ========= ======