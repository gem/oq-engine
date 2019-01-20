Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ===================
checksum32     3,339,350,387      
date           2019-01-20T07:39:36
engine_version 3.4.0-git452d0c6835
============== ===================

num_sites = 5, num_levels = 20

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      50.0              
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
======================= ============================
Name                    File                        
======================= ============================
gsim_logic_tree         `gmmLT_3.xml <gmmLT_3.xml>`_
job_ini                 `job.ini <job.ini>`_        
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_    
======================= ============================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 complex(3,0,4)  12/12           
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =============================================================================== =========== ============================= ============================
grp_id gsims                                                                           distances   siteparams                    ruptparams                  
====== =============================================================================== =========== ============================= ============================
0      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip hypo_depth mag rake ztor
1      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip hypo_depth mag rake ztor
2      AtkinsonBoore2003SInter() YoungsEtAl1997SInter() ZhaoEtAl2006SInter()           rrup        vs30                          hypo_depth mag              
====== =============================================================================== =========== ============================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=11, rlzs=12)
  0,BooreAtkinson2008(): [0 4 8]
  0,CampbellBozorgnia2008(): [1 5 9]
  0,ChiouYoungs2008(): [ 2  6 10]
  0,ZhaoEtAl2006Asc(): [ 3  7 11]
  1,BooreAtkinson2008(): [0 4 8]
  1,CampbellBozorgnia2008(): [1 5 9]
  1,ChiouYoungs2008(): [ 2  6 10]
  1,ZhaoEtAl2006Asc(): [ 3  7 11]
  2,AtkinsonBoore2003SInter(): [0 1 2 3]
  2,YoungsEtAl1997SInter(): [4 5 6 7]
  2,ZhaoEtAl2006SInter(): [ 8  9 10 11]>

Number of ruptures per tectonic region type
-------------------------------------------
====================================================================== ====== ==================== ============ ============
source_model                                                           grp_id trt                  eff_ruptures tot_ruptures
====================================================================== ====== ==================== ============ ============
ssm/shallow/gridded_seismicity_source_4.xml ... ssm/shallow/int_kt.xml 0      Active Shallow Crust 1,100        3,800       
ssm/shallow/gridded_seismicity_source_4.xml ... ssm/shallow/int_kt.xml 1      Active Shallow Crust 1,117        1,117       
ssm/shallow/gridded_seismicity_source_4.xml ... ssm/shallow/int_kt.xml 2      Subduction Interface 3,536        3,536       
====================================================================== ====== ==================== ============ ============

============= ======
#TRT models   3     
#eff_ruptures 5,753 
#tot_ruptures 8,453 
#tot_weight   33,412
============= ======

Slowest sources
---------------
====== ========== ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id  code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========== ==== ===== ===== ============ ========= ========== ========= ========= ======
0      ds_4_10097 P    0     1     100          0.0       0.0        0.0       0         0.0   
0      ds_4_10734 P    1     2     100          0.0       0.0        0.0       0         0.0   
0      ds_4_13441 P    2     3     100          0.0       0.0        0.0       0         0.0   
0      ds_4_13542 P    3     4     100          0.0       0.0        0.0       0         0.0   
0      ds_4_13549 P    4     5     100          0.0       0.0        0.0       0         0.0   
0      ds_4_13974 P    5     6     100          0.0       0.0        0.0       0         0.0   
0      ds_4_1455  P    6     7     100          0.0       0.0        0.0       0         0.0   
0      ds_4_14802 P    7     8     100          0.0       0.0        0.0       0         0.0   
0      ds_4_15201 P    8     9     100          0.0       1.907E-06  0.0       1         0.0   
0      ds_4_16265 P    9     10    100          0.0       0.0        0.0       0         0.0   
0      ds_4_18232 P    10    11    100          0.0       1.907E-06  0.0       1         0.0   
0      ds_4_1895  P    11    12    100          0.0       0.0        0.0       0         0.0   
0      ds_4_19558 P    12    13    100          0.0       1.431E-06  0.0       1         0.0   
0      ds_4_19649 P    13    14    100          0.0       0.0        0.0       0         0.0   
0      ds_4_19683 P    14    15    100          0.0       0.0        0.0       0         0.0   
0      ds_4_2111  P    15    16    100          0.0       1.669E-06  0.0       1         0.0   
0      ds_4_28780 P    16    17    100          0.0       0.0        0.0       0         0.0   
0      ds_4_314   P    17    18    100          0.0       0.0        0.0       0         0.0   
0      ds_4_32853 P    18    19    100          0.0       0.0        0.0       0         0.0   
0      ds_4_33979 P    19    20    100          0.0       0.0        0.0       0         0.0   
====== ========== ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.0       1     
P    0.0       38    
S    0.0       5     
==== ========= ======

Duplicated sources
------------------
Found 0 source(s) with the same ID and 0 true duplicate(s)

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.09285 0.12186 0.01319 0.23313 3      
split_filter       7.64496 NaN     7.64496 7.64496 1      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ======================================= ========
task               sent                                    received
read_source_models converter=1.14 KB fnames=368 B          60.81 KB
split_filter       srcs=58.92 KB srcfilter=253 B seed=14 B 1.62 MB 
================== ======================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total split_filter       7.64496  7.56641   1     
total read_source_models 0.27856  2.08203   3     
======================== ======== ========= ======