Hazard Japan (HERP model 2014) reduced
======================================

============== ====================
checksum32     2_710_180_929       
date           2020-11-02T09:36:18 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 5, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 300.0), (10.0, 300.0)]}
investigation_time              50.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                3.0                                       
rupture_mesh_spacing            5.0                                       
complex_fault_mesh_spacing      10.0                                      
width_of_mfd_bin                0.1                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     113                                       
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

Input files
-----------
======================= ==============================================
Name                    File                                          
======================= ==============================================
gsim_logic_tree         `gmmLT_sa.xml <gmmLT_sa.xml>`_                
job_ini                 `job.ini <job.ini>`_                          
site_model              `Site_model_Japan.xml <Site_model_Japan.xml>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_                      
======================= ==============================================

Composite source model
----------------------
====== ====================== ====
grp_id gsim                   rlzs
====== ====================== ====
0      '[ZhaoEtAl2006SInter]' [0] 
1      '[ZhaoEtAl2006SInter]' [0] 
====== ====================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ====================== ========= ========== ==============
et_id gsims                  distances siteparams ruptparams    
===== ====================== ========= ========== ==============
0     '[ZhaoEtAl2006SInter]' rrup      vs30       hypo_depth mag
===== ====================== ========= ========== ==============

Slowest sources
---------------
================== ==== ========= ========= ============
source_id          code calc_time num_sites eff_ruptures
================== ==== ========= ========= ============
case_02            N    2.475E-04 1         1           
gs_PSE_CPCF_2_1228 P    2.041E-04 1         26          
================== ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    2.475E-04
P    2.041E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       2      7.406E-04 1%     7.267E-04 7.546E-04
read_source_model  1      0.00345   nan    0.00345   0.00345  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ============================= ========
task              sent                          received
read_source_model                               6.49 KB 
preclassical      srcs=6.8 KB srcfilter=3.35 KB 501 B   
================= ============================= ========

Slowest operations
------------------
========================= ======== ========= ======
calc_47293, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.09267  0.0       1     
composite source model    0.08433  0.0       1     
total read_source_model   0.00345  0.0       1     
total preclassical        0.00148  0.41406   2     
========================= ======== ========= ======