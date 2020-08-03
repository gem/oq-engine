Hazard Calculation for end-to-end hazard+risk
=============================================

============== ===================
checksum32     1_526_146_286      
date           2020-03-13T11:20:04
engine_version 3.9.0-gitfb3ef3a732
============== ===================

num_sites = 1, num_levels = 50, num_rlzs = 4

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 300.0}
investigation_time              15.0              
ses_per_logic_tree_path         1                 
truncation_level                4.0               
rupture_mesh_spacing            20.0              
complex_fault_mesh_spacing      20.0              
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1024              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job_h.ini <job_h.ini>`_                                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================
smlt_path weight  num_realizations
========= ======= ================
b1        1.00000 4               
========= ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================================================ ========== ========== ==============
grp_id gsims                                                                                            distances  siteparams ruptparams    
====== ================================================================================================ ========== ========== ==============
0      '[AkkarBommer2010]'                                                                              rjb        vs30       mag rake      
1      '[AtkinsonBoore2003SInter]' '[LinLee2008SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]' rhypo rrup vs30       hypo_depth mag
====== ================================================================================================ ========== ========== ==============

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.04348   23           23          
1      0.04348   23           23          
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
B         1      P    23           0.00180   0.04348   23          
A         0      P    23           0.00164   0.04348   23          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.00344  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00241 7.182E-05 0.00236 0.00246 2      
read_source_model  0.00205 NaN       0.00205 0.00205 1      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================= ==================================== ========
task              sent                                 received
read_source_model                                      1.86 KB 
preclassical      srcs=2.26 KB params=2 KB gsims=658 B 738 B   
================= ==================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_66854                  time_sec  memory_mb counts
=========================== ========= ========= ======
composite source model      0.08313   0.68359   1     
total preclassical          0.00482   1.28906   2     
store source_info           0.00227   0.0       1     
total read_source_model     0.00205   0.03906   1     
aggregate curves            6.094E-04 0.0       2     
splitting/filtering sources 4.184E-04 0.0       2     
=========================== ========= ========= ======