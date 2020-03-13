Hazard Japan (HERP model 2014) reduced
======================================

============== ===================
checksum32     2_896_463_652      
date           2020-03-13T11:21:30
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 5, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

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
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b11       1.00000 1               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================== ========= ========== ==============
grp_id gsims                  distances siteparams ruptparams    
====== ====================== ========= ========== ==============
0      '[ZhaoEtAl2006SInter]' rrup      vs30       hypo_depth mag
====== ====================== ========= ========== ==============

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.07407   27           27          
====== ========= ============ ============

Slowest sources
---------------
================== ====== ==== ============ ========= ========= ============
source_id          grp_id code num_ruptures calc_time num_sites eff_ruptures
================== ====== ==== ============ ========= ========= ============
case_02            0      N    1            0.00177   1.00000   1.00000     
gs_PSE_CPCF_2_1228 0      P    26           0.00170   0.03846   26          
================== ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
N    0.00177  
P    0.00170  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00241 2.377E-05 0.00239 0.00242 2      
read_source_model  0.00220 NaN       0.00220 0.00220 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================= ========================================== ========
task              sent                                       received
read_source_model                                            6.51 KB 
preclassical      srcs=7.4 KB params=1.21 KB srcfilter=446 B 786 B   
================= ========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66943                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.01235   0.0       1     
total preclassical          0.00481   1.26953   2     
total read_source_model     0.00220   0.0       1     
store source_info           0.00205   0.0       1     
aggregate curves            5.763E-04 0.0       2     
splitting/filtering sources 3.669E-04 0.0       2     
=========================== ========= ========= ======