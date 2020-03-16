Reduced USGS 1998 Hawaii model
==============================

============== ===================
checksum32     4_283_469_194      
date           2020-03-13T11:22:07
engine_version 3.9.0-gitfb3ef3a732
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
pointsource_distance            {'default': 0}    
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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 8               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================================================== ========= ========== ==============
grp_id gsims                                                                                          distances siteparams ruptparams    
====== ============================================================================================== ========= ========== ==============
0      '[YoungsEtAl1997SSlab]'                                                                        rrup      vs30       hypo_depth mag
1      '[BooreEtAl1997GeometricMean]' '[Campbell1997]' '[MunsonThurber1997Hawaii]' '[SadighEtAl1997]' rjb rrup  vs30       mag rake      
2      '[MunsonThurber1997Hawaii]' '[SadighEtAl1997]'                                                 rjb rrup  vs30       mag rake      
====== ============================================================================================== ========= ========== ==============

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.02222   45           45          
1      0.06667   6_945        6_945       
2      0.11538   104          104         
====== ========= ============ ============

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures
========== ====== ==== ============ ========= ========= ============
HLE        1      A    6_945        0.03361   0.06667   6_945       
HLEKAOSFL  2      C    104          0.00731   0.11538   104         
Deep_10014 0      P    45           0.00172   0.02222   45          
========== ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.03361  
C    0.00731  
P    0.00172  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.17997 0.20883 0.00256 0.41011 3      
read_source_model  0.04999 0.05834 0.00225 0.11502 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model converter=996 B fname=341 B srcfilter=12 B 6.2 KB  
preclassical      srcs=5.46 KB params=4.31 KB gsims=1.87 KB  1.06 KB 
================= ========================================== ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66982                  time_sec memory_mb counts
=========================== ======== ========= ======
total preclassical          0.53991  2.58203   3     
splitting/filtering sources 0.49195  1.01953   3     
composite source model      0.17734  0.0       1     
total read_source_model     0.14998  0.73828   3     
store source_info           0.00252  0.0       1     
aggregate curves            0.00128  0.0       3     
=========================== ======== ========= ======