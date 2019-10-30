Reduced USGS 1998 Hawaii model
==============================

============== ===================
checksum32     1,744,669,526      
date           2019-10-23T16:26:34
engine_version 3.8.0-git2e0d8e6795
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.440E-04 6,945        6,945       
1      0.00962   104          104         
2      0.02222   45           45          
====== ========= ============ ============

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures
========== ====== ==== ============ ========= ========= ============
HLEKAOSFL  1      C    104          0.00267   0.00962   104         
Deep_10014 2      P    45           0.00143   0.02222   45          
HLE        0      A    6,945        0.00119   1.440E-04 6,945       
========== ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.00119  
C    0.00267  
P    0.00143  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.05875 0.08093   0.00133 0.15131 3      
preclassical       0.00204 7.864E-04 0.00148 0.00294 3      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=4.15 KB ltmodel=813 B fname=362 B 12.19 KB
preclassical srcs=5.15 KB params=4.11 KB gsims=1.87 KB   1 KB    
============ =========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_44528             time_sec memory_mb counts
====================== ======== ========= ======
composite source model 0.17991  0.0       1     
total SourceReader     0.17625  0.0       3     
aggregate curves       0.00963  0.0       3     
total preclassical     0.00611  0.0       3     
store source_info      0.00224  0.0       1     
====================== ======== ========= ======