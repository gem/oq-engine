Classical PSHA for the southern Pacific Islands reduced
=======================================================

============== ===================
checksum32     1,406,686,210      
date           2019-07-30T15:04:19
engine_version 3.7.0-git3b3dff46da
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
========== ====== ==== ============ ========= ========= ====== =========
source_id  grp_id code num_ruptures calc_time num_sites weight speed    
========== ====== ==== ============ ========= ========= ====== =========
sf_85      1      S    348          0.03203   3.00000   348    10,866   
kt         2      C    3,536        0.02933   5.00000   3,536  120,572  
sf_81      1      S    348          0.02829   3.00000   348    12,301   
sf_84      1      S    262          0.01536   1.00000   262    17,058   
sf_82      1      S    46           0.01251   1.00000   46     3,678    
sf_83      1      S    113          0.01133   1.00000   113    9,973    
ds_4_6534  0      P    100          0.00231   3.00000   100    43,361   
ds_4_482   0      P    100          0.00200   1.00000   100    50,117   
ds_4_18232 0      P    100          0.00198   3.00000   100    50,424   
ds_4_5043  0      P    100          0.00168   2.00000   100    59,452   
ds_4_8502  0      P    100          3.431E-04 4.00000   100    291,474  
ds_4_8499  0      P    100          3.085E-04 4.00000   100    324,135  
ds_4_15201 0      P    100          1.581E-04 4.00000   100    632,625  
ds_4_2111  0      P    100          1.566E-04 1.00000   100    638,402  
ds_4_19558 0      P    100          1.452E-04 1.00000   100    688,720  
ds_4_36349 0      P    100          1.202E-04 1.00000   100    832,203  
ds_4_464   0      P    100          8.225E-05 1.00000   100    1,215,740
========== ====== ==== ============ ========= ========= ====== =========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.02933   1     
P    0.00928   38    
S    0.09951   5     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.02191 0.02378 0.00429 0.06817 7      
read_source_models 0.14714 0.19166 0.02312 0.36789 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== =========================================================== ========
task               sent                                                        received
preclassical       srcs=64.25 KB params=4.96 KB gsims=3.52 KB srcfilter=1.5 KB 2.77 KB 
read_source_models converter=942 B fnames=347 B                                61.97 KB
================== =========================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15525               time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.44143  0.0       3     
total preclassical       0.15335  0.0       7     
managing sources         0.00796  0.0       1     
store source_info        0.00520  0.0       1     
aggregate curves         0.00152  0.0       7     
======================== ======== ========= ======