Hazard Calculation for end-to-end hazard+risk
=============================================

============== ====================
checksum32     3_242_621_847       
date           2020-11-02T09:35:14 
engine_version 3.11.0-git82b78631ac
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
====== =========================== ============
grp_id gsim                        rlzs        
====== =========================== ============
0      '[AkkarBommer2010]'         [0, 1, 2, 3]
1      '[AtkinsonBoore2003SInter]' [1]         
1      '[LinLee2008SInter]'        [3]         
1      '[YoungsEtAl1997SInter]'    [2]         
1      '[ZhaoEtAl2006SInter]'      [0]         
====== =========================== ============

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
A         P    2.232E-04 1         23          
B         P    2.208E-04 1         23          
========= ==== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    4.439E-04
==== =========

Information about the tasks
---------------------------
================== ====== ========= ====== ========= =========
operation-duration counts mean      stddev min       max      
preclassical       2      7.422E-04 0%     7.350E-04 7.493E-04
read_source_model  1      0.00276   nan    0.00276   0.00276  
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
calc_47202, maxmem=1.0 GB time_sec memory_mb counts
========================= ======== ========= ======
importing inputs          0.07561  0.78906   1     
composite source model    0.06963  0.77344   1     
total read_source_model   0.00276  0.03125   1     
total preclassical        0.00148  0.36328   2     
========================= ======== ========= ======