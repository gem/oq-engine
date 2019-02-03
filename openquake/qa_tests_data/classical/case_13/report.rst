Classical PSHA QA test
======================

============== ===================
checksum32     752,446,534        
date           2019-02-03T09:40:03
engine_version 3.4.0-gite8c42e513a
============== ===================

num_sites = 21, num_levels = 26

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
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
aFault_aPriori_D2.1       0.50000 simple(2)       2               
bFault_stitched_D2.1_Char 0.50000 simple(2)       2               
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
====== ========= ==== ====== ====== ============ ========= ========== ========= ========= ======
grp_id source_id code gidx1  gidx2  num_ruptures calc_time split_time num_sites num_split weight
====== ========= ==== ====== ====== ============ ========= ========== ========= ========= ======
1      9_1       X    50,809 50,872 11           0.0       0.0        0.0       0         0.0   
1      9_0       X    50,746 50,809 11           0.0       0.0        0.0       0         0.0   
1      99_1      X    50,656 50,746 11           0.0       1.192E-06  14        1         41    
1      99_0      X    50,566 50,656 11           0.0       1.431E-06  14        1         41    
1      98_1      X    50,518 50,566 11           0.0       1.192E-06  15        1         42    
1      98_0      X    50,470 50,518 11           0.0       1.669E-06  15        1         42    
1      97_1      X    50,438 50,470 11           0.0       1.431E-06  17        1         45    
1      97_0      X    50,406 50,438 11           0.0       1.431E-06  17        1         45    
1      96_1      X    50,371 50,406 11           0.0       1.431E-06  12        1         38    
1      96_0      X    50,336 50,371 11           0.0       1.192E-06  12        1         38    
1      95_1      X    50,292 50,336 11           0.0       3.576E-06  15        1         42    
1      95_0      X    50,248 50,292 11           0.0       1.669E-06  15        1         42    
1      94_1      X    50,080 50,248 11           0.0       1.192E-06  4.00000   1         22    
1      94_0      X    49,912 50,080 11           0.0       1.431E-06  4.00000   1         22    
1      93_1      X    49,882 49,912 11           0.0       1.192E-06  12        1         38    
1      93_0      X    49,852 49,882 11           0.0       1.431E-06  12        1         38    
1      92_1      X    49,832 49,852 11           0.0       1.431E-06  8.00000   1         31    
1      92_0      X    49,812 49,832 11           0.0       1.431E-06  8.00000   1         31    
1      91_1      X    49,768 49,812 11           0.0       1.192E-06  11        1         36    
1      91_0      X    49,724 49,768 11           0.0       1.431E-06  11        1         36    
====== ========= ==== ====== ====== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.0       426   
==== ========= ======

Duplicated sources
------------------
Found 180 source(s) with the same ID and 0 true duplicate(s)
Here is a fake duplicate: 20_1

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 1.11159 0.41180 0.82040 1.40278 2      
split_filter       0.03699 NaN     0.03699 0.03699 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ====================================== ========
task               sent                                   received
read_source_models converter=626 B fnames=234 B           1.46 MB 
split_filter       srcs=1.46 MB srcfilter=253 B seed=14 B 1.4 MB  
================== ====================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 2.22317  3.77734   2     
total split_filter       0.03699  1.77344   1     
======================== ======== ========= ======