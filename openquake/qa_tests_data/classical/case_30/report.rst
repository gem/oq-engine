Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ===================
checksum32     56,125,602         
date           2019-02-03T09:39:42
engine_version 3.4.0-gite8c42e513a
============== ===================

num_sites = 5, num_levels = 20

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
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
b1        1.00000 complex(3,0,4)  12              
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
ssm/shallow/gridded_seismicity_source_4.xml ... ssm/shallow/int_kt.xml 0      Active Shallow Crust 3,800        3,800       
ssm/shallow/gridded_seismicity_source_4.xml ... ssm/shallow/int_kt.xml 1      Active Shallow Crust 1,117        1,117       
ssm/shallow/gridded_seismicity_source_4.xml ... ssm/shallow/int_kt.xml 2      Subduction Interface 3,536        3,536       
====================================================================== ====== ==================== ============ ============

============= ======
#TRT models   3     
#eff_ruptures 8,453 
#tot_ruptures 8,453 
#tot_weight   15,641
============= ======

Slowest sources
---------------
====== ========== ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id  code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========== ==== ===== ===== ============ ========= ========== ========= ========= ======
2      kt         C    348   834   3,536        0.0       0.0        1.00000   0         14,144
1      sf_85      S    274   348   348          0.0       0.0        1.00000   0         348   
1      sf_84      S    206   274   262          0.0       0.0        1.00000   0         262   
1      sf_83      S    153   206   113          0.0       0.0        1.00000   0         113   
1      sf_82      S    112   153   46           0.0       0.0        1.00000   0         46    
1      sf_81      S    38    112   348          0.0       0.0        1.00000   0         348   
0      ds_4_9857  P    37    38    100          0.0       0.0        1.00000   0         10    
0      ds_4_9114  P    36    37    100          0.0       0.0        1.00000   0         10    
0      ds_4_8502  P    35    36    100          0.0       0.0        1.00000   0         10    
0      ds_4_8499  P    34    35    100          0.0       0.0        1.00000   0         10    
0      ds_4_6688  P    33    34    100          0.0       0.0        1.00000   0         10    
0      ds_4_6534  P    32    33    100          0.0       0.0        1.00000   0         10    
0      ds_4_5043  P    31    32    100          0.0       0.0        1.00000   0         10    
0      ds_4_482   P    30    31    100          0.0       0.0        1.00000   0         10    
0      ds_4_464   P    29    30    100          0.0       0.0        1.00000   0         10    
0      ds_4_38515 P    28    29    100          0.0       0.0        1.00000   0         10    
0      ds_4_38372 P    27    28    100          0.0       0.0        1.00000   0         10    
0      ds_4_38367 P    26    27    100          0.0       0.0        1.00000   0         10    
0      ds_4_38209 P    25    26    100          0.0       0.0        1.00000   0         10    
0      ds_4_37967 P    24    25    100          0.0       0.0        1.00000   0         10    
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
read_source_models 0.10019 0.13412 0.01348 0.25467 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================ ========
task               sent                         received
read_source_models converter=939 B fnames=368 B 61.86 KB
================== ============================ ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.30056  2.34766   3     
======================== ======== ========= ======