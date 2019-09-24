Reduced USGS 1998 Hawaii model
==============================

============== ===================
checksum32     4,283,469,194      
date           2019-09-24T15:21:15
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 80, num_rlzs = 8

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
complex_fault_mesh_spacing      10.0              
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
b1        1.00000 complex(1,4,2)  8               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================================================== ========= ========== ==============
grp_id gsims                                                                                          distances siteparams ruptparams    
====== ============================================================================================== ========= ========== ==============
0      '[BooreEtAl1997GeometricMean]' '[Campbell1997]' '[MunsonThurber1997Hawaii]' '[SadighEtAl1997]' rjb rrup  vs30       mag rake      
1      '[MunsonThurber1997Hawaii]' '[SadighEtAl1997]'                                                 rjb rrup  vs30       mag rake      
2      '[YoungsEtAl1997SSlab]'                                                                        rrup      vs30       hypo_depth mag
====== ============================================================================================== ========= ========== ==============

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=21, rlzs=8)>

Number of ruptures per tectonic region type
-------------------------------------------
======================================================================== ====== ============== ============ ============
source_model                                                             grp_id trt            eff_ruptures tot_ruptures
======================================================================== ====== ============== ============ ============
ssm/Area_65m/area_source_gp_HLE.xml ... ssm/gridded_seismicity/point.xml 0      Volcanic       6,945        6,945       
ssm/Area_65m/area_source_gp_HLE.xml ... ssm/gridded_seismicity/point.xml 1      Volcanic_large 104          104         
ssm/Area_65m/area_source_gp_HLE.xml ... ssm/gridded_seismicity/point.xml 2      Deepseismicity 45           45          
======================================================================== ====== ============== ============ ============

============= =====
#TRT models   3    
#eff_ruptures 7,094
#tot_ruptures 7,094
============= =====

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============ ==========
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures speed     
========== ====== ==== ============ ========= ========= ============ ==========
HLEKAOSFL  1      C    104          0.00279   1.00000   104          37,210    
Deep_10014 2      P    45           2.503E-04 1.00000   45           179,756   
HLE        0      A    6,945        2.182E-04 1.00000   6,945        31,835,454
========== ====== ==== ============ ========= ========= ============ ==========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    2.182E-04 1     
C    0.00279   1     
P    2.503E-04 1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ========= ======= =======
operation-duration mean    stddev  min       max     outputs
preclassical       0.00158 0.00151 6.771E-04 0.00333 3      
read_source_models 0.04600 0.05750 0.00177   0.11100 3      
================== ======= ======= ========= ======= =======

Data transfer
-------------
================== ============================================ ========
task               sent                                         received
preclassical       srcs=5.21 KB params=4.28 KB srcfilter=1.9 KB 1 KB    
read_source_models converter=942 B fnames=371 B                 6.4 KB  
================== ============================================ ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1820                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.13799   0.0       3     
total preclassical       0.00474   0.0       3     
store source_info        0.00265   0.0       1     
aggregate curves         8.895E-04 0.0       3     
managing sources         4.599E-04 0.0       1     
======================== ========= ========= ======