Hazard Calculation for end-to-end hazard+risk
=============================================

============== ====================
checksum32     3_242_621_847       
date           2020-11-02T08:40:36 
engine_version 3.11.0-gitd13380ddb1
============== ====================

num_sites = 1, num_levels = 50, num_rlzs = 4

Parameters
----------
=============================== ==========================================
calculation_mode                'preclassical'                            
number_of_logic_tree_samples    0                                         
maximum_distance                {'default': [(1.0, 300.0), (10.0, 300.0)]}
investigation_time              15.0                                      
ses_per_logic_tree_path         1                                         
truncation_level                4.0                                       
rupture_mesh_spacing            20.0                                      
complex_fault_mesh_spacing      20.0                                      
width_of_mfd_bin                0.2                                       
area_source_discretization      10.0                                      
pointsource_distance            None                                      
ground_motion_correlation_model None                                      
minimum_intensity               {}                                        
random_seed                     1024                                      
master_seed                     0                                         
ses_seed                        42                                        
=============================== ==========================================

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
====== ========================= ============
grp_id gsim                      rlzs        
====== ========================= ============
0      [AkkarBommer2010]         [0, 1, 2, 3]
1      [AtkinsonBoore2003SInter] [1]         
1      [LinLee2008SInter]        [3]         
1      [YoungsEtAl1997SInter]    [2]         
1      [ZhaoEtAl2006SInter]      [0]         
====== ========================= ============

Required parameters per tectonic region type
--------------------------------------------
===== ================================================================================================ ========== ========== ==============
et_id gsims                                                                                            distances  siteparams ruptparams    
===== ================================================================================================ ========== ========== ==============
0     '[AkkarBommer2010]'                                                                              rjb        vs30       mag rake      
1     '[AtkinsonBoore2003SInter]' '[LinLee2008SInter]' '[YoungsEtAl1997SInter]' '[ZhaoEtAl2006SInter]' rhypo rrup vs30       hypo_depth mag
===== ================================================================================================ ========== ========== ==============

Slowest sources
---------------
========= ==== ========= ========= ============
source_id code calc_time num_sites eff_ruptures
========= ==== ========= ========= ============
A         P    2.127E-04 1         23          
B         P    2.103E-04 1         23          
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    4.230E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       2      6.979E-04 1%     6.862E-04 7.095E-04
read_source_model  1      0.00251   nan    0.00251   0.00251  
================== ====== ========= ====== ========= =========

Data transfer
-------------
================= ============================== ========
task              sent                           received
read_source_model                                1.84 KB 
preclassical      srcfilter=4.04 KB srcs=2.34 KB 478 B   
================= ============================== ========

Slowest operations
------------------
========================= ======== ========= ======
calc_46488, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.06892  0.85547   1     
composite source model    0.06332  0.83984   1     
total read_source_model   0.00251  0.02734   1     
total preclassical        0.00140  0.37109   2     
========================= ======== ========= ======