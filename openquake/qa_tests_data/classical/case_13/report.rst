Classical PSHA QA test
======================

============== ===================
checksum32     752,446,534        
date           2018-12-13T12:58:03
engine_version 3.3.0-git68d7d11268
============== ===================

num_sites = 21, num_levels = 26

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
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
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
sites                   `qa_sites.csv <qa_sites.csv>`_                              
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========================= ======= =============== ================
smlt_path                 weight  gsim_logic_tree num_realizations
========================= ======= =============== ================
aFault_aPriori_D2.1       0.50000 simple(2)       2/2             
bFault_stitched_D2.1_Char 0.50000 simple(2)       2/2             
========================= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  0,BooreAtkinson2008(): [0]
  0,ChiouYoungs2008(): [1]
  1,BooreAtkinson2008(): [2]
  1,ChiouYoungs2008(): [3]>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== ============ ============
source_model                  grp_id trt                  eff_ruptures tot_ruptures
============================= ====== ==================== ============ ============
aFault_aPriori_D2.1.xml       0      Active Shallow Crust 1,958        1,980       
bFault_stitched_D2.1_Char.xml 1      Active Shallow Crust 2,310        2,706       
============================= ====== ==================== ============ ============

============= ======
#TRT models   2     
#eff_ruptures 4,268 
#tot_ruptures 4,686 
#tot_weight   13,919
============= ======

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======
0      0_0       X    0     65    11           0.0       1.168E-05  0.0       1         0.0   
0      0_1       X    65    130   11           0.0       2.861E-06  0.0       1         0.0   
0      10_0      X    130   290   11           0.0       1.907E-06  0.0       1         0.0   
0      10_1      X    290   450   11           0.0       1.431E-06  0.0       1         0.0   
0      11_0      X    450   666   11           0.0       1.907E-06  0.0       1         0.0   
0      11_1      X    666   882   11           0.0       1.669E-06  0.0       1         0.0   
0      12_0      X    882   1,142 11           0.0       1.431E-06  0.0       1         0.0   
0      12_1      X    1,142 1,402 11           0.0       1.669E-06  0.0       1         0.0   
0      13_0      X    1,402 1,462 11           0.0       1.907E-06  0.0       1         0.0   
0      13_1      X    1,462 1,522 11           0.0       1.669E-06  0.0       1         0.0   
0      14_0      X    1,522 1,582 11           0.0       1.669E-06  0.0       1         0.0   
0      14_1      X    1,582 1,642 11           0.0       1.669E-06  0.0       1         0.0   
0      15_0      X    1,642 1,702 11           0.0       1.431E-06  0.0       1         0.0   
0      15_1      X    1,702 1,762 11           0.0       1.669E-06  0.0       1         0.0   
0      16_0      X    1,762 1,802 11           0.0       1.431E-06  0.0       1         0.0   
0      16_1      X    1,802 1,842 11           0.0       1.669E-06  0.0       1         0.0   
0      17_0      X    1,842 1,874 11           0.0       0.0        0.0       0         0.0   
0      17_1      X    1,874 1,906 11           0.0       0.0        0.0       0         0.0   
0      18_0      X    1,906 2,021 11           0.0       1.669E-06  0.0       1         0.0   
0      18_1      X    2,021 2,136 11           0.0       1.431E-06  0.0       1         0.0   
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.0       426   
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 1.15333 0.34782 0.90738 1.39927 2      
split_filter       0.03905 NaN     0.03905 0.03905 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ====================================== ========
task               sent                                   received
read_source_models converter=776 B fnames=234 B           1.45 MB 
split_filter       srcs=1.46 MB srcfilter=253 B seed=14 B 1.4 MB  
================== ====================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 2.30665  2.39453   2     
total split_filter       0.03905  0.23438   1     
======================== ======== ========= ======