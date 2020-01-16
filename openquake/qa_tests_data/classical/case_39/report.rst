Reduced USGS 1998 Hawaii model
==============================

============== ===================
checksum32     4_283_469_194      
date           2020-01-16T05:31:14
engine_version 3.8.0-git83c45f7244
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
0      0.06667   6_945        6_945       
1      0.11538   104          104         
2      0.02222   45           45          
====== ========= ============ ============

Slowest sources
---------------
========== ====== ==== ============ ========= ========= ============
source_id  grp_id code num_ruptures calc_time num_sites eff_ruptures
========== ====== ==== ============ ========= ========= ============
HLE        0      A    6_945        0.04169   0.06667   6_945       
HLEKAOSFL  1      C    104          0.00666   0.11538   104         
Deep_10014 2      P    45           0.00229   0.02222   45          
========== ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.04169  
C    0.00666  
P    0.00229  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.04968 0.05651 0.00273 0.11239 3      
preclassical       0.19931 0.21323 0.00339 0.42642 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ============================================ ========
task         sent                                         received
SourceReader apply_unc=4.15 KB ltmodel=813 B fname=362 B  8.84 KB 
preclassical params=113.42 KB srcfilter=20 KB srcs=5.2 KB 1.07 KB 
============ ============================================ ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43312                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          0.59793   0.51953   3     
splitting/filtering sources 0.54082   0.0       3     
total SourceReader          0.14903   0.0       3     
composite source model      0.13521   0.0       1     
store source_info           0.00242   0.0       1     
aggregate curves            9.551E-04 0.0       3     
=========================== ========= ========= ======