Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

============== ===================
checksum32     905,885,649        
date           2019-07-30T15:04:29
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 3, num_levels = 17, num_rlzs = 8

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
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
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============== ======= =============== ================
smlt_path      weight  gsim_logic_tree num_realizations
============== ======= =============== ================
SM1            0.50000 complex(2,2)    4               
SM2_a3b1       0.25000 simple(2,0)     2               
SM2_a3pt2b0pt8 0.25000 simple(2,0)     2               
============== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =============================================== ========= ========== =================
grp_id gsims                                           distances siteparams ruptparams       
====== =============================================== ========= ========== =================
0      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' rjb rrup  vs30 z2pt5 dip mag rake ztor
1      '[Campbell2003]' '[ToroEtAl2002]'               rjb rrup             mag              
2      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' rjb rrup  vs30 z2pt5 dip mag rake ztor
3      '[BooreAtkinson2008]' '[CampbellBozorgnia2008]' rjb rrup  vs30 z2pt5 dip mag rake ztor
====== =============================================== ========= ========== =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=16, rlzs=8)>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ======================== ============ ============
source_model       grp_id trt                      eff_ruptures tot_ruptures
================== ====== ======================== ============ ============
source_model_1.xml 0      Active Shallow Crust     15           15          
source_model_1.xml 1      Stable Continental Crust 15           15          
source_model_2.xml 2      Active Shallow Crust     240          240         
source_model_2.xml 3      Active Shallow Crust     240          240         
================== ====== ======================== ============ ============

============= ===
#TRT models   4  
#eff_ruptures 510
#tot_ruptures 510
============= ===

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ====== ======
source_id grp_id code num_ruptures calc_time num_sites weight speed 
========= ====== ==== ============ ========= ========= ====== ======
1         0      P    15           0.00538   9.00000   495    92,017
2         1      P    15           0.00184   3.00000   15     8,154 
========= ====== ==== ============ ========= ========= ====== ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       2     
P    0.00722   2     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00231 3.094E-04 0.00205 0.00275 4      
read_source_models 0.00343 0.00179   0.00145 0.00494 3      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ========================================================= ========
task               sent                                                      received
preclassical       srcs=6.16 KB params=2.74 KB gsims=1.09 KB srcfilter=880 B 1.34 KB 
read_source_models converter=942 B fnames=306 B                              6.71 KB 
================== ========================================================= ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15534               time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.01028   0.0       3     
total preclassical       0.00922   0.0       4     
managing sources         0.00526   0.0       1     
store source_info        0.00205   0.0       1     
aggregate curves         5.660E-04 0.0       4     
======================== ========= ========= ======