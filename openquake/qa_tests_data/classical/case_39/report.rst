Reduced USGS 1998 Hawaii model
==============================

============== ===================
checksum32     4,283,469,194      
date           2019-10-01T07:01:08
engine_version 3.8.0-gitbd71c2f960
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
0      1.00000   6,945        6,945       
1      1.00000   104          104         
2      1.00000   45           45          
====== ========= ============ ============

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============ =========
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures speed    
========== ====== ==== ============ ========= ========= ============ =========
HLEKAOSFL  1      C    104          0.00492   1.00000   104          21,140   
HLE        0      A    6,945        0.00205   1.00000   6,945        3,389,904
Deep_10014 2      P    45           0.00138   1.00000   45           32,638   
========== ====== ==== ============ ========= ========= ============ =========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00205   1     
C    0.00492   1     
P    0.00138   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.04800 0.05722 0.00241 0.11222 3      
preclassical       0.00323 0.00198 0.00168 0.00547 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=4.15 KB ltmodel=813 B fname=362 B 11.79 KB
preclassical srcs=5.17 KB params=4.28 KB gsims=1.87 KB   1 KB    
============ =========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6628              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.14401  0.0       3     
composite source model 0.13171  0.0       1     
total preclassical     0.00970  0.0       3     
store source_info      0.00260  0.0       1     
aggregate curves       0.00110  0.0       3     
====================== ======== ========= ======