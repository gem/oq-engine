Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ===================
checksum32     1,406,686,210      
date           2019-09-24T15:21:19
engine_version 3.7.0-git749bb363b3
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

  <RlzsAssoc(size=41, rlzs=12)>

Number of ruptures per tectonic region type
-------------------------------------------
====================================================================== ====== ==================== ============ ============
source_model                                                           grp_id trt                  eff_ruptures tot_ruptures
====================================================================== ====== ==================== ============ ============
ssm/shallow/gridded_seismicity_source_4.xml ... ssm/shallow/int_kt.xml 0      Active Shallow Crust 1,100        3,800       
ssm/shallow/gridded_seismicity_source_4.xml ... ssm/shallow/int_kt.xml 1      Active Shallow Crust 1,117        1,117       
ssm/shallow/gridded_seismicity_source_4.xml ... ssm/shallow/int_kt.xml 2      Subduction Interface 3,536        3,536       
====================================================================== ====== ==================== ============ ============

============= =====
#TRT models   3    
#eff_ruptures 5,753
#tot_ruptures 8,453
============= =====

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============ =======
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========== ====== ==== ============ ========= ========= ============ =======
sf_81      1      S    348          0.01831   3.00000   348          19,003 
sf_85      1      S    348          0.01752   3.00000   348          19,858 
sf_83      1      S    113          0.01639   1.00000   113          6,896  
kt         2      C    3,536        0.01558   5.00000   3,536        227,011
sf_84      1      S    262          0.01060   1.00000   262          24,706 
sf_82      1      S    46           0.00674   1.00000   46           6,820  
ds_4_6534  0      P    100          3.469E-04 3.00000   100          288,268
ds_4_19558 0      P    100          3.181E-04 1.00000   100          314,416
ds_4_482   0      P    100          2.809E-04 1.00000   100          356,053
ds_4_464   0      P    100          2.532E-04 1.00000   100          394,944
ds_4_5043  0      P    100          2.460E-04 2.00000   100          406,425
ds_4_8502  0      P    100          2.413E-04 4.00000   100          414,457
ds_4_8499  0      P    100          2.387E-04 4.00000   100          419,011
ds_4_2111  0      P    100          2.117E-04 1.00000   100          472,332
ds_4_15201 0      P    100          1.800E-04 4.00000   100          555,537
ds_4_36349 0      P    100          1.137E-04 1.00000   100          879,309
ds_4_18232 0      P    100          1.063E-04 3.00000   100          940,427
========== ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.01558   1     
P    0.00254   38    
S    0.06957   5     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ========= ======= =======
operation-duration mean    stddev  min       max     outputs
preclassical       0.00707 0.00996 4.072E-04 0.02740 14     
read_source_models 0.11791 0.14598 0.02228   0.28594 3      
================== ======= ======= ========= ======= =======

Data transfer
-------------
================== =============================================== ========
task               sent                                            received
preclassical       srcs=70.05 KB srcfilter=12.44 KB params=9.93 KB 4.78 KB 
read_source_models converter=942 B fnames=368 B                    61.99 KB
================== =============================================== ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1831                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.35373   0.0       3     
total preclassical       0.09896   0.0       14    
aggregate curves         0.00382   0.0       14    
store source_info        0.00273   0.0       1     
managing sources         6.623E-04 0.0       1     
======================== ========= ========= ======