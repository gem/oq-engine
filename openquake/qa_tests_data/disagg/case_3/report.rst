test for POE_TOO_BIG
====================

============== ====================
checksum32     96_663_792          
date           2020-11-02T08:41:03 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 1, num_levels = 200, num_rlzs = 6

Parameters
----------
=============================== ==================================================================================================================================================================================================================================================================================================
calculation_mode                'preclassical'                                                                                                                                                                                                                                                                                    
number_of_logic_tree_samples    0                                                                                                                                                                                                                                                                                                 
maximum_distance                {'Active Shallow Crust': [(1.0, 200.0), (10.0, 200.0)], 'Stable Shallow Crust': [(1.0, 200.0), (10.0, 200.0)], 'Subduction Inslab': [(1.0, 200), (10.0, 200)], 'Subduction Interface': [(1.0, 200), (10.0, 200)], 'Volcanic': [(1.0, 100), (10.0, 100)], 'default': [(1.0, 200.0), (10.0, 200.0)]}
investigation_time              50.0                                                                                                                                                                                                                                                                                              
ses_per_logic_tree_path         1                                                                                                                                                                                                                                                                                                 
truncation_level                3.0                                                                                                                                                                                                                                                                                               
rupture_mesh_spacing            15.0                                                                                                                                                                                                                                                                                              
complex_fault_mesh_spacing      15.0                                                                                                                                                                                                                                                                                              
width_of_mfd_bin                0.1                                                                                                                                                                                                                                                                                               
area_source_discretization      15.0                                                                                                                                                                                                                                                                                              
pointsource_distance            None                                                                                                                                                                                                                                                                                              
ground_motion_correlation_model None                                                                                                                                                                                                                                                                                              
minimum_intensity               {}                                                                                                                                                                                                                                                                                                
random_seed                     23                                                                                                                                                                                                                                                                                                
master_seed                     0                                                                                                                                                                                                                                                                                                 
ses_seed                        42                                                                                                                                                                                                                                                                                                
=============================== ==================================================================================================================================================================================================================================================================================================

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
====== =================== ====
grp_id gsim                rlzs
====== =================== ====
0      [BindiEtAl2011]     [0] 
0      [BindiEtAl2014Rhyp] [1] 
0      [CauzziEtAl2014]    [2] 
1      [BindiEtAl2011]     [3] 
1      [BindiEtAl2014Rhyp] [4] 
1      [CauzziEtAl2014]    [5] 
====== =================== ====

Required parameters per tectonic region type
--------------------------------------------
===== ========================================================== ============== ========== ==========
et_id gsims                                                      distances      siteparams ruptparams
===== ========================================================== ============== ========== ==========
0     '[BindiEtAl2011]' '[BindiEtAl2014Rhyp]' '[CauzziEtAl2014]' rhypo rjb rrup vs30       mag rake  
1     '[BindiEtAl2011]' '[BindiEtAl2014Rhyp]' '[CauzziEtAl2014]' rhypo rjb rrup vs30       mag rake  
===== ========================================================== ============== ========== ==========

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
f1        C    0.00158   1         477         
p1        P    1.853E-04 1         156         
p3        P    1.814E-04 1         156         
p2        P    1.745E-04 1         156         
p4        P    1.714E-04 1         156         
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
C    0.00158  
P    7.126E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =======
operation-duration counts mean      stddev min       max    
preclassical       5      9.479E-04 59%    6.320E-04 0.00207
read_source_model  2      0.00298   3%     0.00287   0.00309
================== ====== ========= ====== ========= =======

Data transfer
-------------
================= ============================ ========
task              sent                         received
read_source_model converter=664 B fname=210 B  5.82 KB 
preclassical      srcfilter=9.8 KB srcs=7.9 KB 1.17 KB 
================= ============================ ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46532, maxmem=1.2 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          1.06159  0.0       1     
composite source model    1.05680  0.0       1     
total read_source_model   0.00596  0.62500   2     
total preclassical        0.00474  0.37500   5     
========================= ======== ========= ======