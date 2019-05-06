Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ===================
checksum32     1,670,864,910      
date           2019-05-03T06:43:58
engine_version 3.5.0-git7a6d15e809
============== ===================

num_sites = 5, num_levels = 20, num_rlzs = 12

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
b1        1.00000 complex(4,3,0)  12              
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================================================= =========== ============================= ============================
grp_id gsims                                                                                   distances   siteparams                    ruptparams                  
====== ======================================================================================= =========== ============================= ============================
0      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip hypo_depth mag rake ztor
1      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' '[ChiouYoungs2008]' '[ZhaoEtAl2006Asc]' rjb rrup rx vs30 vs30measured z1pt0 z2pt5 dip hypo_depth mag rake ztor
2      '[AtkinsonBoore2003SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]'             rrup        vs30                          hypo_depth mag              
====== ======================================================================================= =========== ============================= ============================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=11, rlzs=12)
  0,'[BooreAtkinson2008]': [0 1 2]
  0,'[CampbellBozorgnia2008]': [3 4 5]
  0,'[ChiouYoungs2008]': [6 7 8]
  0,'[ZhaoEtAl2006Asc]': [ 9 10 11]
  1,'[BooreAtkinson2008]': [0 1 2]
  1,'[CampbellBozorgnia2008]': [3 4 5]
  1,'[ChiouYoungs2008]': [6 7 8]
  1,'[ZhaoEtAl2006Asc]': [ 9 10 11]
  2,'[AtkinsonBoore2003SInter]': [0 3 6 9]
  2,'[YoungsEtAl1997SInter]': [ 1  4  7 10]
  2,'[ZhaoEtAl2006SInter]': [ 2  5  8 11]>

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
#tot_weight   15,641
============= ======

Slowest sources
---------------
====== ========== ==== ===== ===== ============ ========= ========= ======
grp_id source_id  code gidx1 gidx2 num_ruptures calc_time num_sites weight
====== ========== ==== ===== ===== ============ ========= ========= ======
2      kt         C    348   834   3,536        7.80653   5.00000   31,627
1      sf_81      S    38    112   348          2.098E-04 3.00000   602   
1      sf_85      S    274   348   348          1.845E-04 3.00000   602   
0      ds_4_18232 P    10    11    100          2.384E-05 3.00000   17    
0      ds_4_8499  P    34    35    100          2.313E-05 4.00000   20    
0      ds_4_36349 P    23    24    100          2.289E-05 1.00000   10    
0      ds_4_15201 P    8     9     100          2.170E-05 4.00000   20    
0      ds_4_464   P    29    30    100          2.050E-05 1.00000   10    
0      ds_4_482   P    30    31    100          1.907E-05 1.00000   10    
1      sf_84      S    206   274   262          1.526E-05 1.00000   262   
0      ds_4_19558 P    12    13    100          1.454E-05 1.00000   10    
1      sf_82      S    112   153   46           1.287E-05 1.00000   46    
0      ds_4_6534  P    32    33    100          1.287E-05 3.00000   17    
0      ds_4_2111  P    15    16    100          1.240E-05 1.00000   10    
0      ds_4_8502  P    35    36    100          8.106E-06 4.00000   20    
0      ds_4_5043  P    31    32    100          7.153E-06 2.00000   14    
1      sf_83      S    153   206   113          5.484E-06 1.00000   113   
0      ds_4_9857  P    37    38    100          0.0       0.0       0.0   
0      ds_4_9114  P    36    37    100          0.0       0.0       0.0   
0      ds_4_6688  P    33    34    100          0.0       0.0       0.0   
====== ========== ==== ===== ===== ============ ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    7.80653   1     
P    1.862E-04 38    
S    4.280E-04 5     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
read_source_models 0.12046 0.15199 0.02162 0.29547 3      
preclassical       0.33067 1.59561 0.00171 7.82182 24     
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ============================================================ ========
task               sent                                                         received
read_source_models converter=939 B fnames=368 B                                 61.86 KB
preclassical       srcs=77.6 KB params=16.1 KB gsims=11.66 KB srcfilter=5.11 KB 7.5 KB  
================== ============================================================ ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total preclassical       7.93612  3.19922   24    
total read_source_models 0.36137  0.0       3     
managing sources         0.00886  0.0       1     
aggregate curves         0.00355  0.0       24    
store source_info        0.00234  0.0       1     
======================== ======== ========= ======