QA test for disaggregation case_2
=================================

============== ===================
checksum32     131,107,173        
date           2018-12-13T12:57:19
engine_version 3.3.0-git68d7d11268
============== ===================

num_sites = 2, num_levels = 1

Parameters
----------
=============================== =================
calculation_mode                'disaggregation' 
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              1.0              
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
=============================== =================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============== ======= =============== ================
smlt_path      weight  gsim_logic_tree num_realizations
============== ======= =============== ================
source_model_1 0.50000 simple(2,1)     2/2             
source_model_2 0.50000 simple(2,1)     2/2             
============== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      YoungsEtAl1997SSlab()                 rrup        vs30                    hypo_depth mag   
1      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=4)
  0,YoungsEtAl1997SSlab(): [0 1]
  1,BooreAtkinson2008(): [0]
  1,ChiouYoungs2008(): [1]
  2,BooreAtkinson2008(): [2]
  2,ChiouYoungs2008(): [3]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Subduction Intraslab 1,815        1,815       
source_model_1.xml 1      Active Shallow Crust 3,630        3,630       
source_model_2.xml 2      Active Shallow Crust 1,420        1,420       
================== ====== ==================== ============ ============

============= =====
#TRT models   3    
#eff_ruptures 6,865
#tot_ruptures 6,865
#tot_weight   1,964
============= =====

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      2         A    0     4     1,815        0.0       2.80068    0.0       121       0.0   
1      1         A    4     8     1,815        0.0       1.89045    0.0       121       0.0   
1      3         A    8     12    1,815        0.0       2.47917    0.0       121       0.0   
2      1         S    0     2     1,420        0.0       0.00274    0.0       15        0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       3     
S    0.0       1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.03083 0.02082 0.01611 0.04556 2      
split_filter       0.12899 NaN     0.12899 0.12899 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ====================================== ========
task               sent                                   received
read_source_models converter=776 B fnames=210 B           5.29 KB 
split_filter       srcs=4.09 KB srcfilter=253 B seed=14 B 86.99 KB
================== ====================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       0.12899  0.91016   1     
total read_source_models 0.06167  0.07422   2     
======================== ======== ========= ======