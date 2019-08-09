test for POE_TOO_BIG
====================

============== ===================
checksum32     3,490,620,350      
date           2019-07-30T15:03:56
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 1, num_levels = 200, num_rlzs = 6

Parameters
----------
=============================== ==============================================================================================================================================================
calculation_mode                'preclassical'                                                                                                                                                
number_of_logic_tree_samples    0                                                                                                                                                             
maximum_distance                {'default': 200.0, 'Stable Shallow Crust': 200.0, 'Active Shallow Crust': 200.0, 'Volcanic': 100.0, 'Subduction Interface': 200.0, 'Subduction Inslab': 200.0}
investigation_time              50.0                                                                                                                                                          
ses_per_logic_tree_path         1                                                                                                                                                             
truncation_level                3.0                                                                                                                                                           
rupture_mesh_spacing            5.0                                                                                                                                                           
complex_fault_mesh_spacing      5.0                                                                                                                                                           
width_of_mfd_bin                0.1                                                                                                                                                           
area_source_discretization      15.0                                                                                                                                                          
ground_motion_correlation_model None                                                                                                                                                          
minimum_intensity               {}                                                                                                                                                            
random_seed                     23                                                                                                                                                            
master_seed                     0                                                                                                                                                             
ses_seed                        42                                                                                                                                                            
=============================== ==============================================================================================================================================================

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
========= ======= ================= ================
smlt_path weight  gsim_logic_tree   num_realizations
========= ======= ================= ================
complex   0.33000 simple(3,0,0,0,0) 3               
point     0.67000 simple(3,0,0,0,0) 3               
========= ======= ================= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================== ============== ========== ==========
grp_id gsims                                                      distances      siteparams ruptparams
====== ========================================================== ============== ========== ==========
0      '[BindiEtAl2011]' '[BindiEtAl2014Rhyp]' '[CauzziEtAl2014]' rhypo rjb rrup vs30       mag rake  
1      '[BindiEtAl2011]' '[BindiEtAl2014Rhyp]' '[CauzziEtAl2014]' rhypo rjb rrup vs30       mag rake  
====== ========================================================== ============== ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=18, rlzs=6)>

Number of ruptures per tectonic region type
-------------------------------------------
============================= ====== ==================== ============ ============
source_model                  grp_id trt                  eff_ruptures tot_ruptures
============================= ====== ==================== ============ ============
source_model_test_complex.xml 0      Active Shallow Crust 2,308        2,308       
source_model_test_point.xml   1      Active Shallow Crust 624          624         
============================= ====== ==================== ============ ============

============= =====
#TRT models   2    
#eff_ruptures 2,932
#tot_ruptures 2,932
============= =====

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ====== =======
source_id grp_id code num_ruptures calc_time num_sites weight speed  
========= ====== ==== ============ ========= ========= ====== =======
f1        0      C    2,308        0.00494   2.00000   2,464  498,854
p2        1      P    156          0.00220   1.00000   156    70,782 
p3        1      P    156          1.926E-04 1.00000   156    809,791
p1        1      P    156          1.662E-04 1.00000   156    938,754
========= ====== ==== ============ ========= ========= ====== =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
C    0.00494   1     
P    0.00256   4     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.00288 0.00105 0.00182 0.00393 3      
read_source_models 0.04238 0.05704 0.00205 0.08271 2      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================== ========================================================== ========
task               sent                                                       received
preclassical       params=6.8 KB srcs=6.31 KB gsims=1.41 KB srcfilter=1.07 KB 1.09 KB 
read_source_models converter=628 B fnames=216 B                               6.27 KB 
================== ========================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15502               time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.08476   0.0       2     
total preclassical       0.00863   0.54297   3     
store source_info        0.00209   0.0       1     
managing sources         0.00130   0.0       1     
aggregate curves         4.241E-04 0.0       3     
======================== ========= ========= ======